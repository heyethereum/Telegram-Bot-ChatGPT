# Telegram-Bot-ChatGPT

**Running chatGPT.py in the background**
nohup python3 chatGPT.py >> output.txt &

**Check if script is running**
ps aux | grep chatGPT.py

**Tail the output of chatGPT**
tail -f -n500 output.txt
