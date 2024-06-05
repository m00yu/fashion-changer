# Webcam Fashion Changer

## Overview
- This project is a webcam fashion-changer application that can segment the hair or clothes from a live webcam feed and apply user-defined color to the segmented area.
- Finding one's personal color is very costful. Nearly 100,000 KRW per session.
- To help you **discover the colors that suit you best quickly and easily**, this application allows you to **change your hair color and clothing color**.
- Find your perfect match!
  
### Features
- Real-time **Hair** segmentation: Segments hair from a live webcam feed.
- **Cloth** segmentation: Segments cloth from a webcam-captured image.
- Interactive Color Change: Experiment with **different hair and clothing colors in real-time**.
- Two models available: Users can choose between head segmentation and clothes segmentation.
  
### Model 1) Hair-chainger (Real-Time)
![시연영상](https://github.com/m00yu/fashion-changer/blob/main/assets/hair.gif)

### Model 2) Cloth-changer
![시연영상](https://github.com/m00yu/fashion-changer/blob/main/assets/cloth.gif)

## How to use
- Clone this repository
   ```bash
    git clone https://github.com/m00yu/fashion-changer.git
    cd fashion-changer
  ```   
- Then simply run the below command.
  ```bash
    bash server.sh
  ```
  This will automatically pull docker image from docker hub and run the docker container in the background.
  <br/> Once the server is running, open your web browser and navigate to http://127.0.0.1 to access the application.
  <br/> Page loading may take few seconds.
- To stop container, run the below command.
  ```bash
    docker stop server
  ```
- To remove container, run the below command.
  ```bash
    docker container rm server
  ```
  Conflict may happen if you do not remove the 'server' container, and trying to run `bash server.sh` again.
  
## Pretrained Models
Please download model checkpoints from the below link.
<br/> https://drive.google.com/drive/folders/1qwBuv3tRUuUhi5HLUqmPsqrSLdcBw85s?usp=sharing
<br/> Create **fashion-changer/models/** directory, then place model weights to the **fashion-changer/models/** directory 


---
## Contributing
### Candidates to Improve
- You can update to a better performing segmentation model
- You can also introduce a new segmentation model altogether. For example, segmenting glasses or cap.
- You might want to improve the web page better.

### How to contribute
- Welcome contributions to improve this project. Here are some ways you can contribute:
- Report Bugs: Use the issue tracker to report bugs.
- Suggest Features: Use the issue tracker to suggest features.
- Submit Pull Requests: Fork the repository, create a branch, make your changes, and submit a pull request.
---
