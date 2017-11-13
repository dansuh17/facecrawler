FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -y python3-pip python3-dev curl wget xvfb libgtk-3-dev libdbus-glib-1-2 \
    && pip3 install --upgrade pip

# install firefox
RUN curl 'https://ftp.mozilla.org/pub/firefox/releases/56.0/linux-x86_64/en-US/firefox-56.0.tar.bz2' \
      -o firefox.tar.bz2 \
      && bunzip2 firefox.tar.bz2 \
      && tar xf firefox.tar \
      && rm firefox.tar

# add path to firefox folder
ENV PATH=/firefox:$PATH
RUN echo $PATH

# download geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.19.0/geckodriver-v0.19.0-linux64.tar.gz
RUN tar -xvf geckodriver*
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin

# set workspace
RUN mkdir -p /tmp/crawler
WORKDIR /tmp/crawler

# copy project files into the workspace
COPY . /tmp/crawler
RUN chmod +x entrypoint.sh

# install dependencies
RUN pip3 install -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python3", "insta_crawler.py"]

