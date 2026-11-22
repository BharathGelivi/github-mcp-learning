# NVIDIA NIM Coding agent

A small terminal travel assistant backed by NVIDIA NIM. It can answer travel
questions and use a read-only `ls` tool to list files and folders inside this
project. Conversation history is kept in memory for the duration of the process.

## Run

1. Install Python 3.9 or newer.
2. Install the dependency:

   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Add your NVIDIA API key to `.env` (keep it private):

   ```dotenv
   NVIDIA_API_KEY=your-nvidia-api-key
   ```
4. Start the loop:

   ```powershell
   py agent.py
   ```

Optionally set `NVIDIA_MODEL` to another model available to your NVIDIA API
account. The default is `nvidia/nemotron-3.5-bolt-e4b`.

Ask to list files or folders in the project to try `ls`. The tool only accepts
project-relative paths and cannot write files or run shell commands. Type `exit`
or `quit` to end the conversation.
