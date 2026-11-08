# Optional: a real phone number, or Asterisk

**Not tested by the course team.** These paths are optional and are not needed for the course or the certificate.
A real phone number needs an account with a telephony provider and costs money; check the provider's current
prices before you start. Never use these paths to record real callers without their consent.

## 1. A real phone number (a provider's media stream)

Many providers can send the audio of a phone call to your app over a WebSocket. Twilio calls this *Media Streams*
(https://www.twilio.com/docs/voice/media-streams). The idea is the same for every provider:

1. Buy a phone number in the provider's console, and set its voice instructions to open a media stream to
   `wss://<your public address>/twilio` (for Twilio: a `<Connect><Stream>` instruction).
2. Make your laptop reachable from the internet with a tunnel (for example Cloudflare Tunnel or ngrok). Close the
   tunnel when you finish.
3. Add a second WebSocket route to `larkspeech/ivr/app.py` that speaks the provider's format. For Twilio:
   - the provider sends JSON messages; `"event": "media"` carries `media.payload`: base64 of 8 kHz G.711 mu-law
     audio. Decode it with `base64.b64decode`, then `audio.mulaw_decode` (in `larkspeech/audio.py`), and feed the
     samples to `CallSession.feed` in 160-sample frames;
   - keypad tones arrive as `"event": "dtmf"` with `dtmf.digit` (handle them as the test phone's `dtmf` messages);
   - to speak, encode each prompt with `audio.mulaw_encode`, base64 it and send
     `{"event": "media", "streamSid": ..., "media": {"payload": ...}}`;
   - `"event": "stop"` ends the call: write the call record.
4. Call the number from your phone. The audio is already 8 kHz: the IVR hears exactly what the course measured.

What changes on a real line: network delay (add it to the latency budget), echo of the IVR's own voice (keep the
caller's audio off while a prompt plays, as the test phone does), and real noise.

## 2. Asterisk and a softphone (stretch)

Asterisk (https://www.asterisk.org/) is an open-source phone system that many contact centres use. It can send a
call's audio to an external app with its *AudioSocket* or *External Media* features. A typical lab setup: Asterisk
in a container, a free softphone on your laptop registered to it, and a dial plan that sends one extension to the
IVR. This needs Docker and some telephony knowledge; the course does not run it.
