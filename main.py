import os
import openai
import flask
from dotenv import load_dotenv
from colorama import Fore, Style
from flask import Flask
from flask_cors import CORS
app = Flask (__name__)
CORS(app, supports_credentials=True)

# load values from the .env file
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """You are an AI assistant who is an expert in Finance and investing for 'Kairos financial'.
Some information about 'Kairos financial':
 "We Are Building for Your Success.
We are a diverse group of veteran bankers, wealth managers, designers, and fintech operators. Our team and advisors have worked at some of the leading organizations in the world.
GENERATIONAL WEALTH STARTS HERE
Wealth Management for The Rest of Us
No more gatekeeping by the financial elite. Just simple, relatable, and proven ways to build your wealth.
You know how to invest, where to invest and what is the best way to save money. You can provide advice on just finance related topics.
There are hundreds of financial products out there. We show you what piece of the financial puzzle you are missing on your way to building wealth.

What's Most Important
Life is haasrd, we get that. We start by tackling your most urgent needs first - i.e. let's get rid of that credit card debt today!
What Can Be Improved
Not all financial companies, products, and features are made equally. Just like the 1% always have the latest and greatest, we will make sure your personal finances are as fine-tuned as a Ferrari.

Personalized Advice
With just a few simple questions, we are able to create personalized plans for you. Not getting exactly what you need? Live chat with our advisors is always available.
Optimize Over Time
Did you know Sears had a bank?! Imagine still having your money with them. We will always be looking for what can be improved.

Holistic Financial Plan
Financial health is more than just the stock market. We help you navigate the entire spectrum of the financial world: savings, investment, debt, & insurance.
We're here to help you build your wealth - and your dreams.
Hi! we'd love to hear from you.
For the quickest access to our team, please log into your account and use our chat feature!
You can also email us at:
hello@kairos.financial
Or leave us a message here."
If you are unable to provide an answer to a question, please respond with the phrase "Sorry, I am just a simple finance bot"
Please aim to be as helpful, creative, and friendly as possible in all of your responses.
You can use https://www.kairos.financial/ for financial services.
Do not use any external URLs in your answers. Do not refer to any blogs in your answers.
Format any lists on individual lines with a dash and a space in front of each item.
Save user personal information.
"""
ANSWER_SEQUENCE = "\nAI:"
QUESTION_SEQUENCE = "\nHuman: "
TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# This limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10


def get_response(prompt):
    """
    Get a response from the model using the prompt

    Parameters:
        prompt (str): The prompt to use to generate the response

    Returns the response from the model
    """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return response.choices[0].text


def get_moderation(question):
    """
    Check the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None


        
def errors(new_question):
        x = ""
        # check if the question is safe
        errors = get_moderation(new_question)
        if errors:
            (
                Fore.RED
                + Style.BRIGHT
                + "Sorry, you're question didn't pass the moderation check:"
            )
            for error in errors:
                x = x+error
            print(Style.RESET_ALL)
            return x

# keep track of previous questions and answers
        
def Answer(new_question, previous_questions, previous_answers):
        assert len(previous_answers) == len(previous_questions)
        # build the previous questions and answers into the prompt
        context = ""
        for i in range(min(len(previous_questions), MAX_CONTEXT_QUESTIONS)):
            context += QUESTION_SEQUENCE + previous_questions[i] + ANSWER_SEQUENCE + previous_answers[i]

        # add the new question at the end of the context
        context += QUESTION_SEQUENCE + new_question + ANSWER_SEQUENCE

        # get the response from the model using the instruction and the context
        response = get_response(INSTRUCTIONS + context)

        # add the new question and answer to the list of previous questions and answers
        previous_questions.append(new_question)
        previous_answers.append(response)

       
        return response, previous_questions, previous_answers


def main():
    
    
    app.run("0.0.0.0", 9000, debug=False)
        
 
       
def call_chat_gpt(question, previous_questions, previous_answers):
    errors = get_moderation(question)
    if errors:
        return errors, previous_questions, previous_answers
    answer, new_previous_questions, new_previous_anwers = Answer(question, previous_questions, previous_answers)
    return answer, new_previous_questions, new_previous_anwers


@app.route("/chatbot", methods=["POST"])
def chatbot():
    """
    input:
    {
        "question": "How can I integrate lightning in my btc network?",
        "previous_questions": "all_prev_questions, context, etc..."
    }

    output:
    {
        
    }
    """

    payload = flask.request.json
    question = payload.get("question")
    prevous_questions = payload.get("previous_questions", [])
    prevous_answers = payload.get("previous_answers", [])

    answer, prev_questions, prev_answers = call_chat_gpt(question, prevous_questions, prevous_answers)
    return flask.jsonify({"answer": answer, "previous_questions": prev_questions, 'previous_answers': prev_answers})


if __name__ == "__main__":
    main()
