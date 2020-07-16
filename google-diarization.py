from google.cloud import speech_v1p1beta1
from google.cloud import storage
import io, sys, getopt, json, csv, time, string, os
import pandas as pd
import data_wrangling

#TODO: Create function to get arguments from command line (i.e. the file)
#TODO: Create function to upload blob (file) to GCP
#TODO: Create function for sample_long_running_recognize
#TODO: Create function to wrangle data
        #This could maybe be 2/3 functions that get called by one function

# Defining some variables
bucket_name = 'audio_analsis' #accidentally mispelled the bucket name lolol

def getArgs(argv):
    #this allows the user to enter some variables, including username and password so that isnt hard coded also returns a usage statement
    input = ''
    
    try:
        opts, args = getopt.getopt(argv,"hi:",["input="])
    except getopt.GetoptError:
        print('usage: <path_to_file> -i <input> ')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: <path_to_file>  -i <input> ')
            sys.exit()
        elif opt in ("-i", "--input"):
            input = arg

    return input

def upload_blob_to_gcp(bucket_name, input_file, destination_blob_name):
    
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(input_file)

    print('File {} uploaded to {}.'.format(
        input_file,
        destination_blob_name))

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

    # local_file_path = 'resources/commercial_mono.wav'

    # If enabled, each word in the first alternative of each result will be
    # tagged with a speaker tag to identify the speaker.
    enable_speaker_diarization = True

    # Optional. Specifies the estimated number of speakers in the conversation.
    diarization_speaker_count = 3

    #It was giving me this error before: Must use single channel (mono) audio, but WAV header indicates 2 channels.
    audio_channel_count = 2
    
    #If enabled, it will detect punctuation.
    enable_automatic_punctuation = True

    # The language of the supplied audio
    language_code = "en-US"
    config = {
        "enable_speaker_diarization": enable_speaker_diarization,
        # "diarization_speaker_count": diarization_speaker_count,
        "language_code": language_code,
        "enable_automatic_punctuation": enable_automatic_punctuation,
        "audio_channel_count": audio_channel_count,
    }
    
    if upload_method == 'local':
        with io.open(audio_file, "rb") as f:
            content = f.read()
            audio = {"content": content}
    elif upload_method == 'uri':
        uri = audio_file
        audio = {"uri": uri}

    operation = client.long_running_recognize(config, audio)

    #print(u"Waiting for operation to complete...")
    response = operation.result()
    #print(u"Done!")

    return response

def main():
    argv = sys.argv[1:]
    input_file = getArgs(argv)
    
    file_path, file_name = os.path.split(input_file)
    
    # Uploading file to GCP Bucket
    upload_blob_to_gcp(bucket_name, input_file, file_name)
    print('uploaded file')

    # Running running the recognize API
    uri = 'gs://' + bucket_name + '/' + file_name
    response = sample_long_running_recognize(uri, 'uri')
    print('ran recognize')

    # Start disecting the response, json-ish, file
    cols = ["source_file", "transcript_id", "word", "end_sentence", "start", "stop", "speaker_tag"]
    master = data_wrangling.create_df(response, file_name, cols)
    master_with_sentences = data_wrangling.separate_sentences(master, cols)
    silence_list = data_wrangling.silence(master_with_sentences)


    # Merge the individual sentences together
    cols_sentence_master = ["sentence", "sentence_id", "speaker_tag","num_speakers", "start_time", "stop_time", "silence"]
    sentence_master = data_wrangling.create_sentences(master_with_sentences, cols_sentence_master, silence_list)
    print('done wrangling')

    # Exporting output to csv
    out_file = 'data/outputs/' + file_name[:-4] + '.csv'
    sentence_master.to_csv(out_file, index = False)
    print('exported to csv')

if __name__ == "__main__":
    main()