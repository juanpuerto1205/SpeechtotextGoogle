# GCP Speaker Diarization

Google speech-to-text API provides speaker diarization capabilities alongside their transcriptions. I've put together this easy to follow notebook that allows you to send audio files through GCP's 'long_running_recognize' to perform operation, to perform asynchronous speech recognition (amongst other things), and return structured ```.csv``` files with the output of the API.

In order to get started there are a couple of things you need to do.

1. Install Google Cloud's suite of tools in python `pip install --upgrade google-cloud-speech`
2. Create a new project on GCP
3. Create a billing account. You need to put payment info so you can use the services
4. Once you have a billing account, you can __Enable the API you want to use__
5. Create credentials for that API service. 
	* You'll get a JSON file with your creds in it
6. Export that creds file to your bashrc with: `export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"`

Now you should be able to start up jupyter using `jupyter notebook` and run through the entire notebook. 
