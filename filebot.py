import json
import asyncio
import re
import configparser
import argparse
from modules.file_summary import create_file_summaries
from modules.find_info import find_relevant_info
from modules.find_info import answer_prompt
from modules.file_ranker import rank_files, get_file_answers

# Answer user prompt
async def answer_user_prompt(relevant_info):
    """Generate a response to the user's prompt based on the relevant info."""
    if not relevant_info:
        return "I'm sorry, I couldn't find any relevant files to answer your question. Please rephrase or try another search."
    else:
        response = "Answer: {}".format(relevant_info)
        return response

# Extract file paths from response
def extract_file_paths(response):
    """Extract file paths from the response using regular expressions."""
    pattern = r"(filebot-store-000\S*)`"
    file_paths = re.findall(pattern, response)
    return file_paths

# Extract file paths from response
def extract_file_paths(response):
    """Extract file paths from the response using regulpattern = r"(filebot-store-000[^\n]*?)(?=[`'\"]?\n|$)"ar expressions."""
    pattern = r"\[(.*?)\]"
    file_paths = re.findall(pattern, response)
    return file_paths

async def main_async():
    parser = argparse.ArgumentParser(description='Run filebot with the specified model.')
    parser.add_argument('--model', type=str, default="gpt-3.5-turbo", help='Which model to use: gpt4 or gpt-3.5-turbo (default is gpt-3.5-turbo)')
    parser.add_argument('--num-files', type=int, default=3, help='Number of top files to consider (default is 3)')

    args = parser.parse_args()
    model_name = args.model

    config = configparser.ConfigParser()
    config.read('filebot.config')
    file_summaries_path = config['OPTIONS'].get('RelativeFileSummariesPath', '')
    file_store_path = config['OPTIONS'].get('RelativeFileStorePath', '')
    await create_file_summaries(file_store_path, file_summaries_path)

    while True:
        user_prompt = input("\033[92mPrompt:\033[0m ")
        relevant_info = await find_relevant_info(user_prompt)

        response = await answer_user_prompt(relevant_info)

        # Extract file paths
        file_paths = extract_file_paths(response)

        if file_paths:

            # Rank and get top files as per user's choice
            top_files = await rank_files(file_paths, args.num_files)

            # Asynchronously get answers for the top 3 files
            answers = await get_file_answers(top_files, user_prompt, answer_prompt)

            # Display the results
            print("\nTop answers from relevant files:")
            for index, (file, answer) in enumerate(answers, start=1):
                print(f"{index}. {answer}\nsource: {file}\n\n")
            print("")

            while True:
                # Ask the user to select a file
                file_choice = input("Please select a file by typing its number or press 'Enter' to skip or select another: ")

                # If the user presses 'Enter' without choosing a file, break to outer loop
                if file_choice.strip() == '':
                    break

                selected_index = int(file_choice) - 1

                # Ensure valid selection
                if selected_index < 0 or selected_index >= len(file_paths):
                    print("\033[38;5;208mInvalid selection\033[0m")
                    continue

                # Use the selected file
                selected_file = re.sub(r'\.\d+$', '', file_paths[selected_index])
                answer = await answer_prompt(selected_file, user_prompt, answer_type='final_answer')
                print(f"\n\n{answer}")
                print(f"\033[1;97m\nsource: {selected_file}\033[0m")
                print("\n\n")

        else:
            print(f"\033[38;5;208mNo files found\033[0m\n\n{response}")

if __name__ == '__main__':
    asyncio.run(main_async())