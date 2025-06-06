import bluetooth_ble  # For G1’s dual BLE
import lc3_decoder   # To handle LC3 audio
import whisper       # Speech-to-text
import nlp_model     # Context analysis
import time
import openai        # Import OpenAI SDK
import hashlib
import os
import json

# Connect to G1’s dual BLE (left and right arms)
ble_left = bluetooth_ble.connect("G1_LEFT_ARM")
ble_right = bluetooth_ble.connect("G1_RIGHT_ARM")

class ProactiveAI:
    def __init__(self):
        self.whisper = whisper.load_model("tiny")  # Fast speech-to-text
        self.nlp = nlp_model.load("distilbert-base")  # Lightweight NLP
        self.buffer = []

    def start_listening(self):
        # Tell G1 to turn on the right mic (no TouchBar wait)
        ble_right.send_command([0x0E, 0x01])  # Enable mic
        response = ble_right.receive()  # Expect [0x0E, 0xC9, 0x01] for success
        if response[1] != 0xC9:
            print("Mic failed to start!")
            return

        while True:  # Loop forever for proactivity
            self.listen_and_process()

    def listen_and_process(self):
        # Get 30s of LC3 audio (G1’s max per chunk)
        audio_chunk = []
        start_time = time.time()
        while time.time() - start_time < 30:
            packet = ble_right.receive()  # [0xF1, seq, audio_data]
            if packet[0] == 0xF1:
                audio_chunk.append(packet[2:])  # Collect audio data

        # Decode LC3 to raw audio
        raw_audio = lc3_decoder.decode(audio_chunk)

        # Convert to text
        text = self.whisper.transcribe(raw_audio)
        if text and text["confidence"] > 0.9:
            # Analyze context
            context = self.nlp.predict_intent(text)
            if context and context["confidence"] > 0.95:
                # Get and display answer
                answer = self.get_answer(context)
                if answer:
                    self.display_answer(answer)

        # Restart mic for next chunk (looping past 30s)
        ble_right.send_command([0x0E, 0x00])  # Disable mic
        time.sleep(0.1)  # Brief pause
        ble_right.send_command([0x0E, 0x01])  # Re-enable mic

    def get_answer(self, context):
        # Use OpenAI to get a real answer from the context with caching and fallback
        if context["intent"] == "question":
            topic = context['entities']['topic']
            prompt = f"User asked: {topic}\nProvide a helpful, concise response."
            cache_key = hashlib.md5(prompt.encode()).hexdigest()
            cache_path = os.path.join("cache", f"{cache_key}.json")

            # Try to read from cache
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r") as f:
                        cached = json.load(f)
                        return cached.get("answer")
                except Exception as e:
                    print(f"Failed to read cache: {e}")

            # If not cached, query OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",  # o4-mini or similar lightweight model
                    messages=[
                        {"role": "system", "content": "You are an assistant for smart glasses. Keep answers short and useful."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.5,
                    max_tokens=100
                )

                answer_text = response.choices[0].message.content.strip()

                # Cache the result
                os.makedirs("cache", exist_ok=True)
                with open(cache_path, "w") as f:
                    json.dump({"answer": answer_text}, f)

                return answer_text

            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback answer
                return f"Sorry, I couldn't get a full answer right now. Here's what I understood: {topic}"

        return None

    def display_answer(self, answer):
        # Split into 488-pixel lines, 5 lines per screen
        lines = split_text(answer, width=488, font_size=21)
        screens = [lines[i:i+5] for i in range(0, len(lines), 5)]

        for screen_idx, screen in enumerate(screens):
            packets = self.pack_screen(screen, screen_idx, len(screens))
            for packet in packets:
                ble_left.send_command(packet)  # Left first
                if ble_left.receive_ack():    # Wait for ack
                    ble_right.send_command(packet)  # Then right

    def pack_screen(self, screen_lines, current_page, max_pages):
        # Build 0x4E packets per G1 protocol
        packets = []
        seq = 0
        total_packets = len(screen_lines) // 3 + 1  # Rough split
        for i in range(0, len(screen_lines), 3):
            chunk = screen_lines[i:i+3]  # Up to 3 lines per packet
            packet = [
                0x4E,              # Command
                seq,               # Sequence
                total_packets,     # Total packets
                i // 3,            # Current packet
                0x31,              # New content + Even AI auto mode
                0x00, 0x00,        # Char pos (simplified)
                current_page,      # Current page
                max_pages          # Total pages
            ] + chunk.encode()     # Add text data
            packets.append(packet)
            seq += 1
        return packets

# Start it up
ai = ProactiveAI()
ai.start_listening()
