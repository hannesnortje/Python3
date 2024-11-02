from transformers import AutoModelForImageClassification, AutoImageProcessor

# Load the MobileNet V2 model from Hugging Face
model = AutoModelForImageClassification.from_pretrained("google/mobilenet_v2_1.0_224")

# Print out the class labels from the model's config
labels = model.config.id2label
print(labels)
