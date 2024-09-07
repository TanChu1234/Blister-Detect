import cv2 as cv
import numpy as np

# Initiate
colors = [
    (255, 0, 0),   # Red
    (0, 255, 0),   # Green
    (0, 0, 255),   # Blue
    (255, 255, 0), # Cyan
    (255, 0, 255), # Magenta
    (0, 255, 255)  # Yellow
]
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 1
thickness = 2
line_type = cv.LINE_AA

def boxes_intersect(box1, box2):
    """Check if two boxes (x, y, w, h) intersect."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    if (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2):
        return True
    return False

def rotate_image(image, angle=45):
    # Get the dimensions of the image
    height, width = image.shape[:2]

    # Calculate the center of the image
    center = (width / 2, height / 2)

    # Calculate the rotation matrix
    matrix = cv.getRotationMatrix2D(center, angle, scale=1.0)

    # Calculate the size of the new image
    cos = np.abs(matrix[0, 0])
    sin = np.abs(matrix[0, 1])

    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))

    # Adjust the rotation matrix to take into account translation
    matrix[0, 2] += (new_width / 2) - center[0]
    matrix[1, 2] += (new_height / 2) - center[1]

    # Perform the actual rotation and display the image
    rotated = cv.warpAffine(image, matrix, (new_width, new_height))
    return rotated

def crop_oval(img, center, axes, angle=0):
    # Create a mask with the same dimensions as the image
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Draw a filled ellipse in the mask with white (255)
    cv.ellipse(mask, center, axes, angle, 0, 360, 255, thickness=-1)

    # Create an all-black image with the same dimensions as the original
    result = np.zeros_like(img)
    
    # Applying the mask: Where mask is true, copy img to result
    mask = mask.astype(bool)
    result[mask] = img[mask]
    return result

def check_crack(roi, white_thresh):
    check = False
    blurred = cv.GaussianBlur(roi, (3, 3), 0)
    # Detect edges using Canny
    edges = cv.Canny(blurred, 30, 110)
    crop_roi = crop_oval(edges, (58,58), (32,20),0)

    white = np.sum(crop_roi == 255)
    # print("white pixel: ",white)
    if white < white_thresh:
        check = True
        # cv.rectangle(img, (x, y), (x+w, y+h), color, 3)
    return check, white
def check_BlemishesAndDefect(roi):
    check = False
    _, lower_mask = cv.threshold(roi, 50, 255, cv.THRESH_BINARY)
    _, upper_mask = cv.threshold(roi, 140, 255, cv.THRESH_BINARY)
    
    # Combine the masks to isolate the range between 30 and 100
    mask = cv.bitwise_and(lower_mask, upper_mask)
    a = 0
    # Apply mask to the original roi
    result = cv.bitwise_and(roi, mask)
    crop_roi = crop_oval(result, (58,58), (40,26),0)

    contours, _ = cv.findContours(crop_roi, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    if contours is not None:
        for contour in contours:
            # print(cv.contourArea(contour))
            if (9 < cv.contourArea(contour) < 300) or cv.contourArea(contour) < 2500:
                a +=1
    if a > 0:
        check = False
    else:
        check = True
    return check, a
def moments(contour):
    # Compute moments
    M = cv.moments(contour)
    area = M['m00']
    
    if area == 0:
        return False  # Avoid division by zero
    
    # Central moments
    mu20 = M['mu20'] / area
    mu02 = M['mu02'] / area
    mu11 = M['mu11'] / area
    
    # Calculate eccentricity
    ecc = np.sqrt(4 * mu11**2 + (mu20 - mu02)**2) / (mu20 + mu02)
    # Determine if it's an oval
    return ecc

def check_oval(roi, eccentricity_threshold):
    check = False
    _, lower_mask = cv.threshold(roi, 50, 255, cv.THRESH_BINARY)
    _, upper_mask = cv.threshold(roi, 140, 255, cv.THRESH_BINARY)
    
    # Combine the masks to isolate the range between 30 and 100
    mask = cv.bitwise_and(lower_mask, upper_mask)
    
    # Apply mask to the original roi
    result = cv.bitwise_and(roi, mask)
    crop_roi = crop_oval(result, (58,58), (40,26),0)

    contours, _ = cv.findContours(crop_roi, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    if contours is not None:
        for contour in contours:
            a = moments(contour)
            if a > eccentricity_threshold:
                check =True
    return check, a

def matchOval(img_path, template, threshold, top_left, bottom_right, segment):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            count +=1
            # color = colors[region_idx] # Use unique color for each region
            cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkCrack(img_path, template, threshold, top_left, bottom_right, segment, white_thresh):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            # roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]+2:y-top_left[1]+h+1, x-x_start+2:x-x_start+w+2]
            roi = rotate_image(roi)
            if region_idx == 0 or region_idx == 5:
                roi = cv.convertScaleAbs(roi, alpha=1, beta=70)
            check, white = check_crack(roi, white_thresh)
            if check  == True:
                count +=1
                # color = colors[region_idx] # Use unique color for each region
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                cv.putText(img, str(white), (x, y-5), font, font_scale, colors[1], thickness, line_type)
            else:
                cv.putText(img, str(white), (x, y-5), font, font_scale, colors[0], thickness, line_type)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkBlemish(img_path, template, threshold, top_left, bottom_right, segment, white_thresh):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            # roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]+2:y-top_left[1]+h+1, x-x_start+2:x-x_start+w+2]

            roi = rotate_image(roi)
         
            if region_idx == 0 or region_idx == 5:
                roi = cv.convertScaleAbs(roi, alpha=1, beta=70)

            check,_ = check_crack(roi, white_thresh)
            check2, blob = check_BlemishesAndDefect(roi)
            if check ==True and check2 == True:
                count +=1
                # color = colors[region_idx] # Use unique color for each region
                cv.putText(img, str(blob), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
            else:
                cv.putText(img, str(blob), (x, y-5), font, font_scale, colors[0], thickness, line_type)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkOval(img_path, template, threshold, top_left, bottom_right, segment, white_thresh,  eccentricity):
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    valid_boxes = []
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image[y-top_left[1]+2:y-top_left[1]+h+1, x-x_start+2:x-x_start+w+2]

            roi = rotate_image(roi)
         
            if region_idx == 0 or region_idx == 5:
                roi = cv.convertScaleAbs(roi, alpha=1, beta=70)

            check, _ = check_crack(roi, white_thresh)
            check2, _ = check_BlemishesAndDefect(roi)
            if check == True and check2 == True:
                check3, ecc = check_oval(roi, eccentricity)
                ecc = round(ecc, 4)
                if check3 == True:
                    count +=1
                    # color = colors[region_idx] # Use unique color for each region
                    cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                    cv.putText(img, str(ecc), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                else:
                    cv.putText(img, str(ecc), (x, y-5), font, font_scale, colors[0], thickness, line_type)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count 

def all(img_path, template, threshold, top_left, bottom_right, segment, white_thresh, eccentricity):
    good = 0
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    w, h = template.shape[::-1]
    
    for region_idx in range(segment):
        valid_boxes = []
        count = 0
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            # roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]+2:y-top_left[1]+h+1, x-x_start+2:x-x_start+w+2]

            roi = rotate_image(roi)
         
            if region_idx == 0 or region_idx == 5:
                roi = cv.convertScaleAbs(roi, alpha=1, beta=70)
            check, _ = check_crack(roi, white_thresh)
            check2, _ = check_BlemishesAndDefect(roi)
            if check == True and check2 == True:
                check3, ecc = check_oval(roi, eccentricity)
                ecc = round(ecc, 4)
                if check3 == True:
                    count +=1
                    cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
        if count == 10:
            good += 1
    print(good)
    return img, count   