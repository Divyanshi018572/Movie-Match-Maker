FROM python:3.11

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Install the Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Hugging Face Spaces expose port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Make the startup script executable
RUN chmod +x start.sh

# Run the incredibly fast single-server script!
CMD ["./start.sh"]
