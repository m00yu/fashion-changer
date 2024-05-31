from fastapi import File, UploadFile, Request, FastAPI
from fastapi.templating import Jinja2Templates
import base64
from test import *
from io import BytesIO
from process import *

PATH = "./model/cloth_segm.pth"
device = 'cpu'
net = load_seg_model(PATH, device=device)
net.eval() # 필요한가?

app = FastAPI()
templates = Jinja2Templates(directory="templates")
palette = get_palette(4)

@app.get("/")
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
  
@app.post("/upload")
def upload(request: Request, file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open("uploaded_" + file.filename, "wb") as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    base64_encoded_image = base64.b64encode(contents).decode("utf-8")
    img = Image.open(BytesIO(contents))
    exif = img._getexif()
    if exif:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        if orientation in exif:
            if exif[orientation] == 3:
                img = img.rotate(180, expand=True)
            elif exif[orientation] == 6:
                img = img.rotate(270, expand=True)
            elif exif[orientation] == 8:
                img = img.rotate(90, expand=True)
    img = img.convert('RGB')
    combined_image_data  = generate_mask(img, net=net, palette=palette, device=device)
    base64_encoded_image = base64.b64encode(combined_image_data).decode("utf-8")
       
    # _input = torch.stack([transform(img)])
    # output = net(_input).argmax().tolist()

    # if output == 0:
    #     result = "Cat"
    # else:
    #     result = "Dog"

    # return templates.TemplateResponse("display.html", {"request": request, "result":result, "myImage":base64_encoded_image})
    return templates.TemplateResponse("display.html", {"request": request, "myImage": base64_encoded_image})
