from network import U2NET, modelv2

import os
from PIL import Image, ExifTags
import cv2
import gdown
import argparse
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.transforms.functional as TF

from collections import OrderedDict
from options import opt

from io import BytesIO


def load_checkpoint(model, checkpoint_path):
    if not os.path.exists(checkpoint_path):
        print("----No checkpoints at given path----")
        return
    model_state_dict = torch.load(checkpoint_path, map_location=torch.device("cpu"))
    new_state_dict = OrderedDict()
    for k, v in model_state_dict.items():
        name = k[7:]  # remove `module.`
        new_state_dict[name] = v

    model.load_state_dict(new_state_dict)
    print("----checkpoints loaded from path: {}----".format(checkpoint_path))
    return model


def get_palette(num_cls):
    """ Returns the color map for visualizing the segmentation mask.
    Args:
        num_cls: Number of classes
    Returns:
        The color map
    """
    n = num_cls
    palette = [0] * (n * 3)
    for j in range(0, n):
        lab = j
        palette[j * 3 + 0] = 0
        palette[j * 3 + 1] = 0
        palette[j * 3 + 2] = 0
        i = 0
        while lab:
            palette[j * 3 + 0] |= (((lab >> 0) & 1) << (7 - i))
            palette[j * 3 + 1] |= (((lab >> 1) & 1) << (7 - i))
            palette[j * 3 + 2] |= (((lab >> 2) & 1) << (7 - i))
            i += 1
            lab >>= 3
    return palette


class Normalize_image(object):
    """Normalize given tensor into given mean and standard dev

    Args:
        mean (float): Desired mean to substract from tensors
        std (float): Desired std to divide from tensors
    """

    def __init__(self, mean, std):
        assert isinstance(mean, (float))
        if isinstance(mean, float):
            self.mean = mean

        if isinstance(std, float):
            self.std = std

        self.normalize_1 = transforms.Normalize(self.mean, self.std)
        self.normalize_3 = transforms.Normalize([self.mean] * 3, [self.std] * 3)
        self.normalize_18 = transforms.Normalize([self.mean] * 18, [self.std] * 18)

    def __call__(self, image_tensor):
        if image_tensor.shape[0] == 1:
            return self.normalize_1(image_tensor)

        elif image_tensor.shape[0] == 3:
            return self.normalize_3(image_tensor)

        elif image_tensor.shape[0] == 18:
            return self.normalize_18(image_tensor)

        else:
            assert "Please set proper channels! Normlization implemented only for 1, 3 and 18"




def apply_transform(img):
    transforms_list = []
    transforms_list += [transforms.ToTensor()]
    transforms_list += [Normalize_image(0.5, 0.5)]
    transform_rgb = transforms.Compose(transforms_list)
    return transform_rgb(img)



def generate_mask(input_image, net, palette, color = (255, 0, 0), device = 'cpu'):

    img = input_image

    img_size = img.size
    img = img.resize((768, 768), Image.BICUBIC)
    image_tensor = apply_transform(img)
    image_tensor = torch.unsqueeze(image_tensor, 0)

    alpha_out_dir = os.path.join(opt.output,'alpha')
    cloth_seg_out_dir = os.path.join(opt.output,'cloth_seg')

    os.makedirs(alpha_out_dir, exist_ok=True)
    os.makedirs(cloth_seg_out_dir, exist_ok=True)

    with torch.no_grad():
        output_tensor = net(image_tensor.to(device))
        output_tensor = F.log_softmax(output_tensor[0], dim=1)
        output_tensor = torch.max(output_tensor, dim=1, keepdim=True)[1]
        output_tensor = torch.squeeze(output_tensor, dim=0)
        output_arr = output_tensor.cpu().numpy()

    classes_to_save = []

    # Check which classes are present in the image
    for cls in range(1, 4):  # Exclude background class (0)
        if np.any(output_arr == cls):
            classes_to_save.append(cls)

    # Save alpha masks
    for cls in classes_to_save:
        alpha_mask = (output_arr == cls).astype(np.uint8) * 255
        alpha_mask = alpha_mask[0]  # Selecting the first channel to make it 2D
        alpha_mask_img = Image.fromarray(alpha_mask, mode='L')
        alpha_mask_img = alpha_mask_img.resize(img_size, Image.BICUBIC)
        alpha_mask_img.save(os.path.join(alpha_out_dir, f'{cls}.png'))

    # Save final cloth segmentations
    cloth_seg = Image.fromarray(output_arr[0].astype(np.uint8), mode='P')
    cloth_seg.putpalette(palette)
    cloth_seg = cloth_seg.resize(img_size, Image.BICUBIC)
    cloth_seg.save(os.path.join(cloth_seg_out_dir, 'final_seg.png'))
    
    # Combine the mask with the original image
    mask = cv2.resize(output_arr[0].astype(np.uint8), img_size, interpolation=cv2.INTER_NEAREST)
    mask_colored = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    
    color = np.array(color).reshape(1, 1, 3)
    
    for cls in classes_to_save:
        mask_colored[mask == cls] = color 
    
    original_image = np.array(input_image)
    combined_image = cv2.addWeighted(original_image, 1.0, mask_colored, 1.0, 0)

    combined_image = Image.fromarray(combined_image)
    combined_image.save(os.path.join(cloth_seg_out_dir, 'combined_image.png'))
    
    # Save combined_image to a BytesIO object
    img_byte_arr = BytesIO()
    combined_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr



def check_or_download_model(file_path):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        url = "https://drive.google.com/uc?id=11xTBALOeUkyuaK3l60CpkYHLTmv7k3dY"
        gdown.download(url, file_path, quiet=False)
        print("Model downloaded successfully.")
    else:
        print("Model already exists.")


def load_seg_model(checkpoint_path, device='cpu'):
    net = U2NET(in_ch=3, out_ch=4)
    net = load_checkpoint(net, checkpoint_path)
    net = net.to(device)
    net = net.eval()

    return net

def capture_image_from_webcam():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret:
            # Display the resulting frame
            cv2.imshow('Press space to capture image', frame)
            print("showing")
            if cv2.waitKey(1) == ord(' '):  # Press space to capture image
                break

    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()

    return frame

def build_model(model_path, device)-> nn.Module:
    net = modelv2(pretrained=False).to(device)

    if model_path:
        print(f'[*] Load Model from {model_path}')
        net.load_state_dict(torch.load(model_path, map_location=device))

    return net

def get_mask(image, net, size=224):
    image_h, image_w = image.shape[0], image.shape[1]

    down_size_image = cv2.resize(image, (size, size))
    down_size_image = cv2.cvtColor(down_size_image, cv2.COLOR_BGR2RGB)
    down_size_image = torch.from_numpy(down_size_image).float().div(255.0).unsqueeze(0)
    down_size_image = np.transpose(down_size_image, (0, 3, 1, 2)).to(device)
    down_size_image = TF.normalize(down_size_image, [0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    mask: torch.nn.Module = net(down_size_image)

    # mask = torch.squeeze(mask[:, 1, :, :])
    mask = mask.argmax(dim=1).squeeze()
    mask_cv2 = mask.data.cpu().numpy() * 255
    mask_cv2 = mask_cv2.astype(np.uint8)
    mask_cv2 = cv2.resize(mask_cv2, (image_w, image_h))

    return mask_cv2
def get_mask(image, net, size=224):
    image_h, image_w = image.shape[0], image.shape[1]

    down_size_image = cv2.resize(image, (size, size))
    down_size_image = cv2.cvtColor(down_size_image, cv2.COLOR_BGR2RGB)
    down_size_image = torch.from_numpy(down_size_image).float().div(255.0).unsqueeze(0)
    down_size_image = np.transpose(down_size_image, (0, 3, 1, 2))
    down_size_image = TF.normalize(down_size_image, [0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    mask: torch.nn.Module = net(down_size_image)

    # mask = torch.squeeze(mask[:, 1, :, :])
    mask = mask.argmax(dim=1).squeeze()
    mask_cv2 = mask.data.cpu().numpy() * 255
    mask_cv2 = mask_cv2.astype(np.uint8)
    mask_cv2 = cv2.resize(mask_cv2, (image_w, image_h))

    return mask_cv2


def alpha_image(image, mask, color=(0, 130, 255), alpha=0.5):
    color = np.array(color).reshape(1, 1, 3)
    color_mask = np.zeros((mask.shape[0], mask.shape[1], 3))
    color_mask[np.where(mask != 0)] = color
    alpha_hand = ((1 - alpha) * image + alpha * color_mask).astype(np.uint8)
    alpha_hand = cv2.bitwise_and(alpha_hand, alpha_hand, mask=mask)

    return cv2.add(alpha_hand, image)

def main(args):

    device = 'cuda:0' if args.cuda else 'cpu'

    palette = get_palette(4)
    
    if args.model == "cloth_camera":
        model = load_seg_model(args.checkpoint_path, device=device)
        # webcam으로부터 이미지 받기
        frame = capture_image_from_webcam()
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img = img.convert('RGB')
        cloth_seg = generate_mask(img, net=model, palette=palette, device=device)

    elif args.model == "hair":
        # real time hair segmentation
        model = build_model(args.checkpoint_path, device)
        cam = cv2.VideoCapture(0)

        if not cam.isOpened():
            raise Exception("webcam is not detected")

        while True:
            # ret : frame capture결과(boolean)
            # frame : Capture한 frame

            ret, image = cam.read()

            if ret:
                mask = get_mask(image, model)
                add = alpha_image(image, mask)
                cv2.imshow('frame', add)
                if cv2.waitKey(1) & 0xFF == ord(chr(27)):
                    break

        cam.release()
        cv2.destroyAllWindows()
    else:
        model = load_seg_model(args.checkpoint_path, device=device)
        # local image 사용하기
        img = Image.open(args.image)
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
        cloth_seg = generate_mask(img, net=model, palette=palette, device=device)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Help to set arguments for Cloth Segmentation.')
    parser.add_argument('--model', type=str, help='Path to the input image')
    parser.add_argument('--cuda', action='store_true', help='Enable CUDA (default: False)')
    parser.add_argument('--checkpoint_path', type=str, default='model/cloth_segm.pth', help='Path to the checkpoint file')
    args = parser.parse_args()

    main(args)