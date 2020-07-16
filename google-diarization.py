from google.cloud import speech_v1p1beta1, storage
import io, sys, getopt, json, os
import pandas as pd
# import slack

# GLOBAL VARIABLES
bucket_name = "nes_twist"
# slack_token = os.environ["SLACK_API_TOKEN"]
# sc = slack.WebClient(token=slack_token)
storage_client = storage.Client()


def sample_long_running_recognize(audio_file, upload_method):
    """
    Print confidence level for individual words in a transcription of a short audio
    file
    Separating different speakers in an audio file recording

    Args:
      file_path Path to local audio file, e.g. /path/audio.wav
      storage_uri, e.g 'gs://audio_analsis/jordan_peterson_mono.wav'
      upload_method, which can be either 'local' or 'uri'

    """

    client = speech_v1p1beta1.SpeechClient()

    # If enabled, each word in the first alternative of each result will be
    # tagged with a speaker tag to identify the speaker.
    enable_speaker_diarization = True

    # Optional. Specifies the estimated number of speakers in the conversation.
    #diarization_speaker_count = 3

    #It was giving me this error before: Must use single channel (mono) audio, but WAV header indicates 2 channels.
    audio_channel_count = 2

    #If enabled, it will detect punctuation.
    enable_automatic_punctuation = True

    # The language of the supplied audio
    language_code = "en-US"
    config = {
        "enable_speaker_diarization": enable_speaker_diarization,
        #"diarization_speaker_count": diarization_speaker_count,
        "language_code": language_code,
        "enable_automatic_punctuation": enable_automatic_punctuation,
        "audio_channel_count": audio_channel_count,
    }

    if upload_method == 'local':
        with io.open(audio_file, "rb") as f:
            content = f.read()
            audio = {"content": content}
    elif upload_method == 'uri':
        uri = "gs://" + bucket_name + "/" + audio_file
        audio = {"uri": uri}

    operation = client.long_running_recognize(config, audio)

    print("Waiting for operation on %s to complete..." % str(audio_file))
    response = operation.result()
    print(u"Done!")

    return response

def response2dataframe(response, nombre):
    """
    Once we receive the response from Google's speech API it comes in a format
    called 'LongRunningRecognizeResponse', which is similar to a .json, but not
    really. The general format of the response is as follows (the ones we need
    are marked with *):

    Response

    Results.Alternatives
        Transcript*
        Words
            Start_time
                seconds*
                nano
            End_time
                seconds*
                nano
            Word*
            Speaker_tag*

    This code will parse that response and output a neat data frame where each
    row is a word with metadata about when that word was spoken, who said it,
    where it came from, etc.
    """

    cols = ["source_file", "transcript_id", "word", "end_sentence", "start", "stop", "speaker_tag"]
    master = pd.DataFrame(columns = cols)

    end_punctuation = [".", "!", "?"]
    source_file = nombre
    transcript_id = []
    word = []
    end_sentence = []
    speaker_tag = []
    start = []
    stop = []

    for i in range(len(response.results) - 1):
        transcript_id = i + 1
        for j in range(len(response.results[i].alternatives[0].words)):

            words = response.results[i].alternatives[0].words[j]

            word = words.word

            for character in word:
                if character in end_punctuation:
                    end_sentence = 1
                else:
                    end_sentence = 0

            start = words.start_time.seconds
            stop = words.end_time.seconds
            speaker_tag = response.results[len(response.results) - 1].alternatives[0].words[j].speaker_tag

            data = [source_file, transcript_id, word, end_sentence, start, stop, speaker_tag]
            df = pd.DataFrame([data], columns = cols)

            master = pd.concat([master, df], axis = 0, ignore_index = True)

    # now we need to add the sentence_ids to each word.
    # that way we know which sentence each word belongs to - makes our lives
    # easier for re-constructing the sentences
    cols_sentences = cols + ["sentence_id"]
    master_with_sentence_ids = pd.DataFrame(columns = cols_sentences)

    sentences = pd.DataFrame(columns = ['sentence_id'])

    sentence_id = 1
    time = 30

    for index, row in master.iterrows():

        sentence_data = [sentence_id]
        if row['start'] >= time:
            if row['end_sentence'] == 1:
                time = row['stop'] + 30
                sentence_id = sentence_id + 1

        df1 = pd.DataFrame([sentence_data], columns = ['sentence_id'])
        sentences = pd.concat([sentences, df1], axis = 0, ignore_index = True)

    master_with_sentence_ids = master.assign(sentence_id = sentences)
    return master_with_sentence_ids

def constructSentences(master_with_sentence_ids):
    '''
    Take the word data frame and reconstruct the sentences from that
    then output that data frame
    '''

    cols_sentence_master = ["sentence", "sentence_id", "speaker_tag","num_speakers", "start_time", "stop_time"]# "start_time"]
    sentence_master = pd.DataFrame(columns = cols_sentence_master)

    sentence = ""

    for y in range(1, master_with_sentence_ids['sentence_id'].max() + 1):
        temp = master_with_sentence_ids.loc[master_with_sentence_ids['sentence_id'] == y]

        for index, row in temp.iterrows():
            sentence += row["word"] + " "

        num_speakers = temp['speaker_tag'].nunique()
        speaker = temp['speaker_tag'].value_counts().idxmax()
        start_time = temp['start'].min()
        stop_time = temp['stop'].max()

        data_2 = [sentence, y, speaker, num_speakers, start_time, stop_time]
        df2 = pd.DataFrame([data_2], columns = cols_sentence_master)
        sentence_master = pd.concat([sentence_master, df2], axis = 0, ignore_index = True)

        sentence = ""

    return sentence_master



def main():
    #os.system('export GOOGLE_APPLICATION_CREDENTIALS="/home/vpt5014/neural_elastic_podcast_search/creds.json"')

    blobs = storage_client.list_blobs(bucket_name)
    for blob in blobs:

        response = sample_long_running_recognize(blob.name, upload_method='uri')
        words = response2dataframe(response, blob.name)
        sentences = constructSentences(words)
        fname = blob.name[:-4]
        sentences.to_csv("/home/vpt5014/neural_elastic_podcast_search/data/interim/" + fname + ".csv", index=False)

    # slack_response = sc.chat_postMessage(
    #     channel="#cojama",
    #     text="_madi voice_: *HEY!* Transcription completed. Congrats. Now delete the bucket and save $$$.",
    #     as_user=True,
    #     user='jarvis')
    # assert slack_response["ok"]


# if __name__ == '__main__':
#     try:
#         main()
#     except Exception as e:
#         # slack_response = sc.chat_postMessage(
#         #     channel="#cojama",
#         #     text="Something went wrong. See Exception: %s" % str(e),
#         #     as_user=True,
#         #     user='jarvis')
#         # assert slack_response["ok"]
#         print(e)

if __name__ == '__main__':
    main()
