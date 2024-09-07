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
def pyramid_down_to_level(image, level):
    """
    Generate an image at a specific level of the Gaussian pyramid.
    :param image: The original image.
    :param level: The desired level of the pyramid.
    :return: The image at the specified pyramid level.
    """
    for _ in range(level):
        image = cv.pyrDown(image)
    return image

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

def filterBlack(roi):
    # Convert the image from BGR to HSV
    hsv_image = cv.cvtColor(roi, cv.COLOR_BGR2HSV)
    # Define the range for black color in HSV
    lower_black = np.array([0, 0, 220])
    upper_black = np.array([180, 30, 255])
    # Create a mask for black color
    # Create a mask for black color
    mask = cv.inRange(hsv_image, lower_black, upper_black)
    # Create an inverse mask to get the non-black parts
    inverse_mask = cv.bitwise_not(mask)
    return inverse_mask

def findCenter(roi):
    _, lower_mask = cv.threshold(roi, 150, 255, cv.THRESH_BINARY)
    _, upper_mask = cv.threshold(roi, 210, 255, cv.THRESH_BINARY)
    # Combine the masks to isolate the range between 30 and 100
    mask = cv.bitwise_and(lower_mask, upper_mask)
    # Apply mask to the original roi
    result = cv.bitwise_and(roi, mask)
    contours, _ = cv.findContours(result, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)        
    largest_contour = max(contours, key=cv.contourArea)
    # cv.drawContours(roi, [largest_contour], 0, 255, 1)
    moments = cv.moments(largest_contour)
    if moments["m00"] != 0:
        cX = int(moments["m10"] / moments["m00"])
        cY = int(moments["m01"] / moments["m00"])
    else:
        cX, cY = 0, 0
    return (cX, cY)

def checkIntact(roi, center, thresh):
    check = False
    mask = filterBlack(roi)
    crop_roi = crop_oval(mask, center, (35,22), 45)
    count_non_zero_pixels = cv.countNonZero(crop_roi)
    if count_non_zero_pixels < thresh:
        check = True
    else:
        check = False
    return check, count_non_zero_pixels

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

def check_BlemishesAndDefect(roi, center, minArea, maxArea):
    blob = 0
    check = False
    _, lower_mask = cv.threshold(roi, 150, 255, cv.THRESH_BINARY)
    _, upper_mask = cv.threshold(roi, 200, 255, cv.THRESH_BINARY)
    # Combine the masks to isolate the range between 30 and 100
    mask = cv.bitwise_and(lower_mask, upper_mask)
    # Apply mask to the original roi
    result = cv.bitwise_and(roi, mask)
    center = findCenter(roi)
    cropgray = crop_oval(result, center, (39,26), 45)
    contours, _ = cv.findContours(cropgray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)    
    for contour in contours:
        if minArea < cv.contourArea(contour) < maxArea:
            blob +=1
    if blob > 0:
        check = False
    else:
        check = True
    return check, blob

def check_oval(roi, center, eccentricity):
    check = False
    _, lower_mask = cv.threshold(roi, 150, 255, cv.THRESH_BINARY)
    _, upper_mask = cv.threshold(roi, 200, 255, cv.THRESH_BINARY)
    # Combine the masks to isolate the range between 30 and 100
    mask = cv.bitwise_and(lower_mask, upper_mask)
    # Apply mask to the original roi
    result = cv.bitwise_and(roi, mask)
    cropgray = crop_oval(result, center, (39,26), 45)
    contours, _ = cv.findContours(cropgray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)    
    largest_contour = max(contours, key=cv.contourArea)  
    ecc = moments(largest_contour)
    if ecc > eccentricity:
        check = True
    else: check = False
    
    return check, ecc

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
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[0], 3)
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
        sub_image_color = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[0], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            color_roi = sub_image_color[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            center = findCenter(roi)
            check, pixel = checkIntact(color_roi, center,  white_thresh)
            if check == True:
                count +=1
                # color = colors[region_idx] # Use unique color for each region
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                cv.putText(img, str(pixel), (x, y-5), font, font_scale, colors[1], thickness, line_type)
            else:
                cv.putText(img, str(pixel), (x, y-5), font, font_scale, colors[2], thickness, line_type)
                
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count


def checkBlemish(img_path, template, threshold, top_left, bottom_right, segment, minBlobArea, maxBlobArea):
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
        # sub_image_color = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[0], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            # color_roi = sub_image_color[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            center = findCenter(roi)
            check, blob = check_BlemishesAndDefect(roi, center, minBlobArea, maxBlobArea)
            if check == True:
                count += 1
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                cv.putText(img, str(blob), (x, y-5), font, font_scale, colors[1], thickness, line_type)
            else:
                cv.putText(img, str(blob), (x, y-5), font, font_scale, colors[2], thickness, line_type)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def checkOval(img_path, template, threshold, top_left, bottom_right, segment, eccentricity):
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
        # sub_image_color = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[0], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            # color_roi = sub_image_color[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            center = findCenter(roi)
            check, ecc = check_oval(roi, center, eccentricity)
            if check == True:
                count += 1
                cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
                cv.putText(img, str(round(ecc, 3)), (x, y-5), font, font_scale, colors[1], thickness, line_type)
            else:
                cv.putText(img, str(round(ecc, 3)), (x, y-5), font, font_scale, colors[2], thickness, line_type)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count

def All(img_path, template, threshold, top_left, bottom_right, segment, white_thresh, minBlobArea, MaxBlobArea, eccentricity):
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
        sub_image_color = img[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        sub_image = img_gray[top_left[1]:bottom_right[1], x_start:x_start + segment_width]
        cv.rectangle(img, (x_start, top_left[1]), (x_start + segment_width, bottom_right[1]), colors[0], 3)
        res = cv.matchTemplate(sub_image, template, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # Correct coordinates for original image
            new_box = [int(pt[0]) + x_start, int(pt[1]) + top_left[1], w, h]
            if not any(boxes_intersect(new_box, box) for box in valid_boxes):
                valid_boxes.append(new_box)

        for x, y, w, h in valid_boxes:
            color_roi = sub_image_color[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            roi = sub_image[y-top_left[1]:y-top_left[1]+h, x-x_start:x-x_start+w]
            center = findCenter(roi)
            check, _ = checkIntact(color_roi, center,  white_thresh)
            if check:
                check, _ = check_BlemishesAndDefect(roi, center, minBlobArea, MaxBlobArea)
                if check:
                    check, _ = check_oval(roi, center, eccentricity)
                    if check:
                        count += 1
                        cv.rectangle(img, (x, y), (x+w, y+h), colors[1], 3)
        cv.putText(img, str(count), (x_start, top_left[1]-5), font, font_scale, colors[1], thickness, line_type)
    return img, count
            
