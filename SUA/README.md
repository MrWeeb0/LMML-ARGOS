The Great American Token Mystery

Overview

This repository contains the automated subword tokenizer identification and payload decoding solution for the LMML Tokenizer Challenge ("The Great American Token Mystery").

The objective is to identify an unknown subword tokenizer across major tokenization libraries (tiktoken, Hugging Face transformers, and sentencepiece) by validating against a provided calibration text and token ID array, then decoding an encrypted challenge sequence to recover the CTF flag.

Repository Structure

main.py — Automated multi-family tokenizer probing, calibration validation, and challenge decoding script.

train-input.json / train-output.json — Local calibration verification sample (p50k_base).

test-input.json — Target evaluation payload containing calibration data and challenge tokens.

test-output.json — Generated output artifact containing the identified tokenizer_id and decoded_message.

Requirements & Setup

Ensure Python 3.9+ is installed alongside the required tokenization dependencies:

pip install tiktoken transformers sentencepiece protobuf


Usage

Place test-input.json in the working directory and run:

python main.py


The script will automatically generate test-output.json in the current working directory.

Results Summary

Identified Tokenizer: meta-llama/Meta-Llama-3-8B

Recovered Flag: SIGMOID_LIBERTY
