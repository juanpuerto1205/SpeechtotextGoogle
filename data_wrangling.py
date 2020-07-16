import io, sys, getopt, json, csv, time, string, os
import pandas as pd

def create_df(response, file_name, cols):
    cols = cols
    master = pd.DataFrame(columns = cols)

    end_punctuation = [".", "!", "?"]
    source_file = file_name
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

    return master

def separate_sentences(master, cols):
    cols_sentences = cols + ["sentence_id"]
    master_with_sentences = pd.DataFrame(columns = cols_sentences)

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
    
    master_with_sentences = master.assign(sentence_id = sentences)
    
    return master_with_sentences

def silence(master_with_sentences):
    silence_list = []

    for y in range(1, master_with_sentences['transcript_id'].max() + 1):
        
        temp_silence_start = master_with_sentences.loc[master_with_sentences['transcript_id'] == y + 1]
        temp_silence_stop = master_with_sentences.loc[master_with_sentences['transcript_id'] == y]
        
        if y != master_with_sentences['transcript_id'].max():
            
            silence_start = temp_silence_stop['stop'].max()
            #print("Start: " + str(silence_start))
            
            silence_stop = temp_silence_start['start'].min()
            #print("Stop: " + str(silence_stop) + "\n")
            
            silence = [silence_start, silence_stop]
            #print(silence)
            silence_list.append(silence)
    
    return silence_list

def create_sentences(master_with_sentences, cols_sentence_master, silence_list):
    # silence_list = silence(master_with_sentences)

    sentence_master = pd.DataFrame(columns = cols_sentence_master)
    sentence = ""
    silence = []

    for y in range(1, master_with_sentences['sentence_id'].max() + 1):
        temp = master_with_sentences.loc[master_with_sentences['sentence_id'] == y]
        
        for index, row in temp.iterrows():
            sentence += row["word"] + " "
        
        num_speakers = temp['speaker_tag'].nunique()
        speaker = temp['speaker_tag'].value_counts().idxmax()
        start_time = temp['start'].min()
        stop_time = temp['stop'].max()
        
        for z in range(0, len(silence_list)):
            
            if start_time <= silence_list[z][1] < stop_time:
                silence.append(silence_list[z])
            

        data_2 = [sentence, y, speaker, num_speakers, start_time, stop_time, silence]
        df2 = pd.DataFrame([data_2], columns = cols_sentence_master)
        sentence_master = pd.concat([sentence_master, df2], axis = 0, ignore_index = True)
        
        sentence = ""
        silence = []

    
    return sentence_master