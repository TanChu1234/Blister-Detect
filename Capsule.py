
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
thickness = 3
line_type = cv.LINE_AA

def boxes_intersect(box1, box2):
    """Check if two boxes (x, y, w, h) intersect."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    if (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2):
        return True
    return False

def color(roi, mask, h_threshold, v_threshold):
    check = False
    # Check for color inconsistencies
    hsv = cv.cvtColor(roi, cv.COLOR_BGR2HSV)
    h, _, v = cv.split(hsv)
    # Calculate standard deviation of hue and value
    h_std = np.std(h[mask > 0])
    v_std = np.std(v[mask > 0])
    if  h_threshold-5 < h_std < h_threshold+5 and v_threshold-8 < v_std < v_threshold+8:
        check = True
    else:
        check = False
    return check, [h_std, v_std]

# def yellow(roi, thresh):
#     check = False
#     # Convert the image to HSV color space
#     hsv = cv.cvtColor(roi, cv.COLOR_BGR2HSV)

#     # Define the range for yellow color in HSV
#     lower_yellow = np.array([20, 200, 200])
#     upper_yellow = np.array([30, 255, 255])

#     # Create a mask for yellow color
#     mask = cv.inRange(hsv, lower_yellow, upper_yellow)
#     yellow_pixel_count = np.sum(mask == 255)
#     if yellow_pixel_count > thresh:
#         check = True
#     else:
#         check = False
#     return check, yellow_pixel_count

def areaOfCapsule(roi, minArea, maxArea):
    check = False
    sobelx = cv.Sobel(roi, cv.CV_64F, 1, 0, ksize=3)
    # Apply Sobel operator in the Y direction
    sobely = cv.Sobel(roi, cv.CV_64F, 0, 1, ksize=3)
    # Compute the gradient magnitude
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    # Normalize the gradient magnitude to the range 0 to 255
    gradient_magnitude = np.uint8(255 * gradient_magnitude / np.max(gradient_magnitude))
    # Apply Gaussian blur to reduce noise
    blurred = cv.GaussianBlur(gradient_magnitude, (5, 5), 0)
    img_gray = cv.cvtColor(blurred, cv.COLOR_BGR2GRAY)
    # Apply binary threshold to the gradient magnitude
    _, binary = cv.threshold(img_gray, 30, 150, cv.THRESH_BINARY)
    # Find contours
    contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # Find the largest contour (by area)
    largest_contour = max(contours, key=cv.contourArea)

    # Find the convex hull of the largest contour
    hull = cv.convexHull(largest_contour)
    if minArea < cv.contourArea(hull) < maxArea:
        check = True
    else: check = False
    return check, cv.contourArea(hull)

def matchCapsule(img_path, template, threshold, top_left, bottom_right, segment):
    good = 0
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    templates = [template, cv.flip(template, 1)]
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        count = 0
        valid_boxes = []
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        # sub_image2 = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        for template in templates:
            res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                # Correct coordinates for original image
                new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
                if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                    valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            count += 1
            cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        if count==10:
            good += 1
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, good

def checkColor(img_path, template, threshold, top_left, bottom_right, segment, hue_thresh, value_thresh):
    good = 0
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    templates = [template, cv.flip(template, 1)]
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        count = 0
        valid_boxes = []
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image2 = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        for template in templates:
            res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                # Correct coordinates for original image
                new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
                if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                    valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            roi = sub_image2[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi_gray = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            # mask = np.zeros(roi_gray.shape, np.uint8)
            check, value = color(roi, roi_gray, hue_thresh, value_thresh)
            
            if check == True:
                count += 1
                cv.putText(img, str(np.round(value, 2)), (x, y-20), font, font_scale, colors[1], thickness, line_type)
            # color = colors[region_idx] # Use unique color for each region
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
            else:
                cv.putText(img, str(np.round(value, 2)), (x, y-20), font, font_scale, colors[2], thickness, line_type)
        if count == 10:
            good += 1
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, good

def checkArea(img_path, template, threshold, top_left, bottom_right, segment, hue_thresh, value_thresh, minArea, maxArea):
    good = 0
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    templates = [template, cv.flip(template, 1)]
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        count = 0
        valid_boxes = []
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image2 = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        for template in templates:
            res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                # Correct coordinates for original image
                new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
                if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                    valid_boxes.append(new_box)
        for x, y, w, h in valid_boxes:
            roi = sub_image2[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi_gray = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            check, _ = color(roi, roi_gray, hue_thresh, value_thresh)
            if check == True:
                count += 1
                check_2, area = areaOfCapsule(roi, minArea, maxArea)
                if check_2 == True:  
                    cv.putText(img, str(area), (x, y-20), font, font_scale, colors[1], thickness, line_type)  
                    cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                else:
                    cv.putText(img, str(area), (x, y-20), font, font_scale, colors[2], thickness, line_type)  
        if count == 10:
            good += 1
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, good

def all(img_path, template, threshold, top_left, bottom_right, segment,  hue_thresh, value_thresh, minArea, maxArea):
    good = 0
    total_width = bottom_right[0] - top_left[0]
    segment_width = total_width // segment
    img = cv.imread(img_path)
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    assert img_gray is not None, "file could not be read, check with os.path.exists()"
    templates = [template, cv.flip(template, 1)]
    w, h = template.shape[::-1]
    for region_idx in range(segment):
        count = 0
        valid_boxes = []
        x_start = top_left[0] + region_idx * segment_width
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image2 = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[2], 3)
        for template in templates:
            res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                # Correct coordinates for original image
                new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
                if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                    valid_boxes.append(new_box)
        for x, y, w, h in valid_boxes:
            roi = sub_image2[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi_gray = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            check, _ = color(roi, roi_gray, hue_thresh, value_thresh) 
            if check == True:
                check_2, _ = areaOfCapsule(roi, minArea, maxArea)
                # cv.putText(img, str(area), (x, y-5), font, font_scale, colors[1], thickness, line_type)
                if check_2 == True:  
                    count += 1
                    cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)       
        if count == 10:
            good += 1
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, good
