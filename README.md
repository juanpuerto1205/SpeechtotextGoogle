# GCP Speaker Diarization

Google speech-to-text API provides speaker diarization capabilities alongside their transcriptions. I've put together this easy to follow notebook that allows you to send audio files through GCP's 'long_running_recognize' to perform operation, to perform asynchronous speech recognition (amongst other things), and return structured ```.csv``` files with the output of the API.

In order to get started there are a couple of things you need to do.

1. Clone this repo
2. Install Google Cloud's suite of tools in python `pip install --upgrade google-cloud-speech`
3. Create a new project on GCP
4. Create a billing account. You need to put payment info so you can use the services
5. Once you have a billing account, you can __Enable the API you want to use__
6. Create credentials for that API service. 
	* You'll get a JSON file with your creds in it
7. Export that creds file to your bashrc with: `export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"`


## Usage

There are two ways you can use this: follow it on jupyter notebook or simply run the following on your command line:

```python google-diarization.py -i <input .wav file> ```

This will output a .csv file to the `data/outputs/` directory.

## Spectrum

I created this pipeline with the goal of using it as a tool to supplement Spectrum with the capability of identifying  multiple speaker dialog in a lecture. For those inside the Penn State network that want to learn more about the tool feel free to visit https://dstoolbox.tlt.psu.edu/
