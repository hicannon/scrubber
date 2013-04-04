I = imread('red-wine.jpg');
subplot(2,1,1); 
imshow(I); title('Original Image');

H = fspecial('log',[25 25],.1);
filtered = imfilter(I,H,'replicate');
subplot(2,1,2); 
imshow(filtered); title('Laplacian of Gaussian Image');