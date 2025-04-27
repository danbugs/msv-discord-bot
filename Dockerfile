# Use an official lightweight Python image
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the bot code
COPY bot.py .

# Set the command to run the bot
CMD ["python", "bot.py"]
