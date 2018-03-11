# Blackboard crawler
This is a blackboard crawler that can download all the file attachments and store them in structured folders on your local (or remote) machine for later use.

## How to run
After downloading the repo, open a terminal inside the folder.
Make sure you have python 2.7 installed.
Now you need to install the requirements using pip:
```
pip install -r requirements.txt --user
```

After the dependencies have been installed, you can run the crawler using:

```
scrapy crawl documents --nolog # nolog is optional
```

You will then be asked for your blackboard domain and login information.
If this is entered correctly, the crawler will begin downloading the documents of all your blackboard courses and store them in the `storage/files` folder in the directory.
