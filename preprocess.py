import argparse
import numpy as np
import os
from scipy import misc, ndimage
import matplotlib.pyplot as plt
from collections import defaultdict

LARGE_IMAGE_SIZE = (1080,1920,3)
LARGE_IMAGE_RESCALE = 0.2
MEDIUM_IMAGE_SIZE = (480,640,3)
MEDIUM_IMAGE_RESCALE = 0.5
FINAL_IMAGE_SIZE = (240,384)
FINAL_IMAGE_DIM = (240, 384, 3)

def process_mot(path):
    '''
    1920 x 1080 -> 384 x 216
    640 x 480 -> 320 x 240
    '''
    images = []
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename[-4:] == ".jpg" and "_ds" not in filename:
                full_path = os.path.join(dirpath, filename)
                img = misc.imread(full_path,mode='RGB')
                if img.shape == LARGE_IMAGE_SIZE:
                    img = misc.imresize(img, size=LARGE_IMAGE_RESCALE)
                    img = pad_image(img, FINAL_IMAGE_SIZE)
                elif img.shape == MEDIUM_IMAGE_SIZE:
                    img = misc.imresize(img, size=MEDIUM_IMAGE_RESCALE)
                    img = pad_image(img, FINAL_IMAGE_SIZE)
                else:
                    print("Unexpected shape " + str(img.shape))
                    continue
                output_filename = os.path.join(dirpath, filename[:-4] + "_ds.jpg")
                misc.imsave(output_filename, img)
                images.append(output_filename)
    return images
                
def pad_image(img, pad_size):
    img = img.transpose(2,0,1)
    diff0 = (pad_size[0] - img.shape[1]) / 2
    diff1 = (pad_size[1] - img.shape[2]) / 2
    img = np.asarray([np.pad(x, ((diff0,), (diff1,)), 'constant', constant_values=(np.median(x) ,)) for x in img])
    return img.transpose(1,2,0)

def training_set_mean_stdev(images):
    average_img = np.zeros(FINAL_IMAGE_DIM)
    average_sq_img = np.zeros(FINAL_IMAGE_DIM)
    num_images = float(len(images))
    for img_path in images:
        img = misc.imread(img_path)
        average_img += img / num_images
        average_sq_img += np.asarray([np.square(x) for x in average_img.transpose(2,0,1)]).transpose(1,2,0) / num_images
    mean = np.asarray([np.mean(x) for x in average_img.transpose(2,0,1)])
    # stdev = np.asarray([np.mean(x) for x in average_sq_img.transpose(2,0,1)]) - np.square(mean)
    stdev = np.asarray([0, 0, 0])
    return mean, stdev    
    
def normalize_training_set(images, mean, stdev):
    channel0 = np.ones(FINAL_IMAGE_SIZE) * mean[0]
    channel1 = np.ones(FINAL_IMAGE_SIZE) * mean[1]
    channel2 = np.ones(FINAL_IMAGE_SIZE) * mean[2]
    mean_pixel = np.asarray([channel0, channel1, channel2]).transpose(1,2,0).astype('int8')
    #print mean_pixel.shape
    for img_path in images:
        img = misc.imread(img_path).astype('int8')
        img -= mean_pixel
        output_filename = img_path[:-4] + "_norm"
        np.save(output_filename, img, allow_pickle=False)

def preprocess_labels(path):
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            frame_to_labels = defaultdict(str)
            if filename == "gt.txt":
                with open(os.path.join(dirpath, filename), "r") as f:
                    for line in f:
                        split_line = line.split(",")
                        frame_to_labels[split_line[0]] += line
            for frame in frame_to_labels:
                output_filename = os.path.join(dirpath, frame.zfill(6) + ".txt")
                with open(output_filename, "w") as of:
                    of.write(frame_to_labels[frame])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess images from each sequence")
    parser.add_argument("corpus_path", type=str, help="Path to corpus")
    args = parser.parse_args()
    path = args.corpus_path
    
    images = process_mot(path)
    mean, stdev = training_set_mean_stdev(images)
    normalize_training_set(images, mean, stdev)
    preprocess_labels(path)
