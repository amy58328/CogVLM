import cv2

while True:
    # img_path = input("input image：")
    # img_path = '14.jpg'
    image = cv2.imread(f'./temp.jpg')

    h = image.shape[0]
    w = image.shape[1]


    image = cv2.resize(image,(998 ,998))

    input_arr = input("input coordinate：").strip('[]').split(',')

    x1, y1 = int(input_arr[0]), int(input_arr[1])  
    x2, y2 = int(input_arr[2]), int(input_arr[3])  


    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2) 

    image = cv2.resize(image,(w,h))

    cv2.imshow('Image with Box', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()