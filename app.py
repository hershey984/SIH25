import os
import traceback
from flask import Flask, request, render_template, url_for, redirect, session
from dotenv import load_dotenv

# Import the function to create our main agent from the supervisor folder
from Models.supervisor_agent import create_supervisor_chain

# Load environment variables from a .env file (for the API key)
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Create the supervisor agent chain once when the application starts
supervisor_chain = create_supervisor_chain()


@app.route("/", methods=["GET"])
def home():
    session.clear()
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        query = request.form.get("query", "")
        if not query:
            return redirect(url_for('home'))

        # Invoke the agent executor
        result = supervisor_chain.invoke({"query": query})

        # result is a Pydantic AnalysisResult object — convert to dict
        if result:
            analysis_dict = result.model_dump()
            session['analysis'] = analysis_dict
            return render_template("confirm_analysis.html", analysis=analysis_dict)
        else:
            # fallback in case no result is returned
            final_decision = {"agent_required": "general_query", "query_passed": query}
            feedback_message = "The agent could not analyze the query. Proceeding as general query."
            return render_template("final_result.html", decision=final_decision, message=feedback_message)

    except Exception as e:
        print(traceback.format_exc())
        return render_template("error.html", error=str(e))


@app.route("/confirm", methods=["POST"])
def confirm():
    analysis = session.get('analysis')  # This is now a dict
    user_choice = request.form.get('choice')

    if not analysis:
        return redirect(url_for('home'))

    if user_choice == 'yes':
        final_decision = analysis
        feedback_message = f"Great! Proceeding with the {analysis['agent_required']} agent."
    else:
        manual_agent = request.form.get('manual_agent')
        analysis['agent_required'] = manual_agent
        final_decision = analysis
        feedback_message = f"Understood. Overriding with the {manual_agent} agent."
        session['user_preference'] = manual_agent

    return render_template("final_result.html", decision=final_decision, message=feedback_message)


if __name__ == "__main__":
    app.run(port=3000, debug=True)
