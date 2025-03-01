import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import time
import random
import os

# Initialize camera
cap = cv2.VideoCapture(0)  # Use 0 for built-in camera
cap.set(3, 1280)  # Full width
cap.set(4, 720)   # Full height

detector = HandDetector(detectionCon=0.7, maxHands=1)  # Hand detection

# Function to load images safely
def load_image(path, size):
    if os.path.exists(path):
        img = cv2.imread(path)
        return cv2.resize(img, size)
    else:
        print(f"Warning: Image '{path}' not found.")
        return None

# Load fruit images
apple = load_image("apple.png", (80, 80))
banana = load_image("banana.png", (80, 80))
watermelon = load_image("watermelon.png", (80, 80))
orange = load_image("orange.png", (80, 80))

basket_apple = load_image("basket_apple.png", (150, 100))
basket_banana = load_image("basket_banana.png", (150, 100))
basket_watermelon = load_image("basket_watermelon.png", (150, 100))
basket_orange = load_image("basket_orange.png", (150, 100))

fruit_images = [apple, banana, watermelon, orange]
fruits = ["Apple", "Banana", "Watermelon", "Orange"]
fruit_positions = []
fruit_respawn_timers = [0] * 5  # Respawn timers

# Define baskets
baskets = {
    "Apple": (250, 600, basket_apple),
    "Banana": (500, 600, basket_banana),
    "Watermelon": (750, 600, basket_watermelon),
    "Orange": (1000, 600, basket_orange)
}

score = 0
selected_fruit = None
start_time = time.time()  # Start game timer
game_duration = 60  # 60 seconds game time

# Function to spawn fruits at random positions
def spawn_fruit():
    return [random.randint(100, 1100), random.randint(100, 500)]

for _ in range(5):
    fruit_positions.append(spawn_fruit())

while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)  # Flip for mirror effect

    hands, img = detector.findHands(img)

    # Draw baskets
    for fruit, (x, y, basket_img) in baskets.items():
        if basket_img is not None:
            if y + 100 < img.shape[0] and x + 75 < img.shape[1]:  # Ensure inside frame
                img[y:y+100, x-75:x+75] = basket_img
        cv2.putText(img, fruit, (x - 40, y + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # Respawn fruits after delay
    current_time = time.time()
    for i in range(len(fruit_positions)):
        if fruit_respawn_timers[i] > 0 and current_time - fruit_respawn_timers[i] > 2:  # 2 seconds respawn
            fruit_positions[i] = spawn_fruit()
            fruit_respawn_timers[i] = 0  # Reset timer

    # Draw fruits
    for i, (x, y) in enumerate(fruit_positions):
        if fruit_respawn_timers[i] == 0 and fruit_images[i % len(fruit_images)] is not None:
            fruit_img = fruit_images[i % len(fruit_images)]
            if y + 80 < img.shape[0] and x + 80 < img.shape[1]:  # Prevent out of bounds error
                img[y:y+80, x:x+80] = fruit_img

    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        index_finger = lmList[8][:2]  # Index finger tip coordinates
        thumb = lmList[4][:2]  # Thumb tip coordinates

        distance, _, _ = detector.findDistance(index_finger, thumb, img)

        if distance < 50 and selected_fruit is None:  # Pick up fruit
            for i, (x, y) in enumerate(fruit_positions):
                if abs(index_finger[0] - x) < 60 and abs(index_finger[1] - y) < 60:
                    selected_fruit = i  # Pick up fruit
                    break

        if selected_fruit is not None:
            fruit_positions[selected_fruit] = index_finger  # Move fruit with hand
            fruit_name = fruits[selected_fruit % len(fruits)]
            cv2.putText(img, f"Holding: {fruit_name}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Check if dropped in the correct basket
            basket_x, basket_y, _ = baskets[fruit_name]
            if abs(index_finger[0] - basket_x) < 75 and abs(index_finger[1] - basket_y) < 50:
                score += 10  # Increase score
                fruit_respawn_timers[selected_fruit] = current_time  # Start respawn timer
                selected_fruit = None  # Reset selection

    # Display score and timer
    elapsed_time = int(time.time() - start_time)
    remaining_time = max(0, game_duration - elapsed_time)

    cv2.putText(img, f"Score: {score}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
    cv2.putText(img, f"Time Left: {remaining_time}s", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # Check if time is up
    if remaining_time == 0:
        cv2.putText(img, "YOU WON!", (500, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        cv2.imshow("Fruit Basket Game", img)
        cv2.waitKey(3000)  # Show message for 3 seconds
        break

    cv2.imshow("Fruit Basket Game", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()