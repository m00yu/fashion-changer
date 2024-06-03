from fastapi import File, UploadFile, Request, FastAPI, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import base64
from io import BytesIO
from process import *

CLOTH_PATH = "./model/cloth_segm.pth"
HAIR_PATH = "./model/hairmattenet_v2.pth"
device = 'cpu'

cloth_net = load_seg_model(CLOTH_PATH, device=device)
hair_net = build_model(HAIR_PATH, device)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
palette = get_palette(4)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@app.get("/")
def main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(image_data: str = Form(...), mask_color: str = Form(...), segmentation_type: str = Form(...)):
    image_data = image_data.split(",")[1]  # Remove the 'data:image/png;base64,' part
    contents = base64.b64decode(image_data)
    mask_color_rgb = hex_to_rgb(mask_color)
    
    img = Image.open(BytesIO(contents))
    img = img.convert('RGB')
    img = np.array(img)

    if segmentation_type == 'hair':
        mask = get_mask(img, hair_net)
        combined_image = alpha_image(img, mask, color=mask_color_rgb)
        combined_image = Image.fromarray(combined_image)
        img_byte_arr = BytesIO()
        combined_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
    elif segmentation_type == 'cloth':
        img_byte_arr = generate_mask(Image.fromarray(img), cloth_net, palette, color=mask_color_rgb, device=device)
    
    base64_encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

    return JSONResponse(content={"segmented_image": base64_encoded_image})