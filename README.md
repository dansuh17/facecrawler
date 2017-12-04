# Crawlfish

Distributed, continuous image crawler.

## Requirements

Firefox web browser (gecko driver)

## Running

Creating a virtual environment for python recommended.

`python3 -m venv ./venv`

Then install dependent packages.

`pip3 install -r requirements.txt`

In order to keep the monitoring running, a monitoring server must be set up before crawling node starts.
Start running the monitor server using this command:

`python3 cherryServer.py`

Start crawling using the following command.

`python3 crawler.py --[option] [option_value]`

Avialable options are:
- `--site [site]` target site to crawl (instagram, facebook, etc.)
- `--filter [filter_type]` type of data filter to screen the data (face)
- `--nthread [number_of_threads]` number of threads used to load web driver and start crawling
- `--logpath [folder_name]` folder name to save the logs in

The status of crawling may be monitored using the monitor reader.

`python3 monitor_read.py`
