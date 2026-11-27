use wasm_bindgen::prelude::*;
use a1800_codec::A1800Encoder;

#[wasm_bindgen]
pub fn encode_pcm(pcm: &[i16]) -> Vec<u8> {
    let mut encoder = A1800Encoder::new(16000).unwrap();
    let frame_words = encoder.encoded_frame_size();
    let frame_bytes = frame_words * 2;
    let num_frames = pcm.len() / 320;
    
    let mut output: Vec<u8> = Vec::new();
    
    output.extend_from_slice(&((num_frames * frame_bytes) as u32).to_le_bytes());
    output.extend_from_slice(&16000u16.to_le_bytes());

    for chunk in pcm.chunks_exact(320) {
        //let mut input = [0i16; 320];
        //input[..chunk.len()].copy_from_slice(chunk);
        
        let mut frame_out = vec![0i16; frame_words];
        encoder.encode_frame(chunk, &mut frame_out).unwrap();

        for word in frame_out {
            output.extend_from_slice(&word.to_le_bytes());
        }
    }

    output
}