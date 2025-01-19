import json
import os
from help import llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException


def process_posts(raw_file_path, processed_file_path=None):
    # Use default path if processed_file_path is not provided
    if processed_file_path is None:
        processed_file_path = os.path.join("data", "processed.json")

    # Check if the raw file exists
    if not os.path.exists(raw_file_path):
        raise FileNotFoundError(f"Raw file not found: {raw_file_path}")

    # Check if the output directory exists
    output_dir = os.path.dirname(processed_file_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist

    with open(raw_file_path, encoding="utf-8") as file:
        posts = json.load(file)
        enriched_posts = []
        for post in posts:
            metadata = extract_metadata(post["text"])
            post_with_metadata = post | metadata
            enriched_posts.append(post_with_metadata)

    unified_tags = get_unified_tags(enriched_posts)
    for post in enriched_posts:
        current_tags = post["tags"]
        new_tags = {unified_tags[tag] for tag in current_tags}
        post["tags"] = list(new_tags)

    with open(processed_file_path, mode="w", encoding="utf-8") as outfile:
        json.dump(enriched_posts, outfile, indent=4)


def extract_metadata(post):
    template = '''
    You are given a LinkedIn post. You need to extract number of lines, language of the post and tags.
    1. Return a valid JSON. No preamble. 
    2. JSON object should have exactly three keys: line_count, language and tags. 
    3. tags is an array of text tags. Extract maximum two tags.
    4. Language should be English or mixhindi (mixhindi means hindi + english)
    
    Here is the actual post on which you need to perform this task:  
    {post}
    '''

    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={"post": post})

    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse jobs.")
    return res


def get_unified_tags(posts_with_metadata):
    unique_tags = set()
    # Loop through each post and extract the tags
    for post in posts_with_metadata:
        unique_tags.update(post["tags"])  # Add the tags to the set

    unique_tags_list = ",".join(unique_tags)

    template = '''I will give you a list of tags. You need to unify tags with the following requirements,
    1. Tags are unified and merged to create a shorter list. 
       Example 1: "Jobseekers", "Job Hunting" can be all merged into a single tag "Job Search". 
       Example 2: "Motivation", "Inspiration", "Drive" can be mapped to "Motivation"
       Example 3: "Personal Growth", "Personal Development", "Self Improvement" can be mapped to "Self Improvement"
       Example 4: "Scam Alert", "Job Scam" etc. can be mapped to "Scams"
    2. Each tag should be follow title case convention. example: "Motivation", "Job Search"
    3. Output should be a JSON object, No preamble
    3. Output should have mapping of original tag and the unified tag. 
       For example: {{"Jobseekers": "Job Search",  "Job Hunting": "Job Search", "Motivation": "Motivation"}}
    
    Here is the list of tags: 
    {tags}
    '''
    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    response = chain.invoke(input={"tags": str(unique_tags_list)})
    try:
        json_parser = JsonOutputParser()
        res = json_parser.parse(response.content)
    except OutputParserException:
        raise OutputParserException("Context too big. Unable to parse jobs.")
    return res


if __name__ == "__main__":
    # Update file paths based on your folder structure
    raw_file_path = os.path.join("data", "Raw_data.json")
    processed_file_path = os.path.join("data", "processed.json")

    process_posts(raw_file_path, processed_file_path)
