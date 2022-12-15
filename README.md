# Dash Default Template: MyDashApp

Created on 2022-12-04 18:29:37.158379

Welcome to your [Plotly Dash](https://plotly.com/dash/) App! This is a template for your MyDashApp app.

See the [Dash Documentation](https://dash.plotly.com/introduction) for more information on how to get your app up and running.

## Running the App

Run `src/app.py` and navigate to http://127.0.0.1:8050/ in your browser.

## Building Docker Image and running it youself

`docker build -t <imagename> .`
`docker run -p 8050:8050 <imagename>` -- use `-d` before the port parameter to run in background

## Run from Docker Hub

`docker run -d -p 8050:8050 anguskong/craftershelper:1.0.0`