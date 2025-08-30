from flask import Flask, request, jsonify, render_template
from agents import Agent, Runner, SQLiteSession, handoff
import asyncio
# Vehicle & complaint agents setup
rates_vehicles = [
    {'vehicle_name': 'Citroen C5', 'rate(£)/km': 0.08},
    {'vehicle_name': 'Tesla', 'rate(£)/km': 0.18},
    {'vehicle_name': 'Jeep Avenger', 'rate(£)/km': 0.06}
]

s = ""
for i in rates_vehicles:
    s += ('Vehicle Name:{}; Cost per km (in £):{}'.format(i['vehicle_name'], i['rate(£)/km']))
    s += '\n'
s = s.strip('\n')

vehicle_agent_inst = f"""This agent aims to register a customer for renting out a vehicle. 
The rent for vehicles is given below
{s}.
Display the vehicle details as shown above. 
Then you should ask the following all the questions given below from the customer.

## QUESTIONS
1. Vehicle customer is interested on?
2. License number and Expiry Date. If Expiry Date is less than the system date, raise the issue and ask customer to resubmit.
3. Enter the name of customer.
4. Pickup point and timing.
5. Drop point and timing.
6. UK Mobile Number
Once the user enters the details thank them and wish them a safe journey.

## GUARDRAILS
- Ask the questions mentioned in that order.
- Do not miss out any questions
- Don't add any additional questions other than mentioned above.
"""

complaint_agent_inst = """This agent aims to register the complaints related to the service. 
There are 3 different sections/areas of registering
1. Vehicle complaint: Any issue with the vehicle
2. Charges issue: Issue with the money debited once customer gets the service done.
3. Others

If the issue is "Vehicle complaint", then ask the following questions
1. Vehicle Number
2. Point where the customer is stuck at
3. What is the issue?

Else if, the issue is "Charges issue", then ask the following questions
1. Vehicle Number used
2. Customer Name
3. Driving License
4. What is the issue?

Else, if the issue is "Others", then ask the following questions
1. Customer Name
2. Phone Number UK
3. What is the issue?

Once the user enters the details thank them.

## GUARDRAILS
- Ask the questions mentioned in that order.
- Do not miss out any questions
- Don't add any additional questions other than mentioned above.
"""

# Agents
vehicle_reg = Agent(
    name="Vehicle_Register",
    instructions=vehicle_agent_inst,
)
complaint_reg = Agent(
    name="Complaint_Register",
    instructions=complaint_agent_inst,
)
zoom_cars_agent = Agent(
    name="Zoom Car Assistant",
    instructions="""You are a T Cars- Rental Chatbot assistant agent. 
    Your task is to help the customers in 2 different aspects
    1. Vehicle Register (vehicle_registration): Help customers in registering a vehicle for taking out on rent.
    2. Complaint registering (complaints_registration): Help customers in registering the complaints with respect to 3 different areas- Vehicle complaint, Charges issue, and Others
    """,
    handoffs=[handoff(vehicle_reg), handoff(complaint_reg)]
)

# Flask App
app = Flask(__name__)

# Persistent session
session = SQLiteSession("conversation_comp")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start", methods=["GET"])
def start():
    """Start conversation with Zoom Car Assistant"""
    result = asyncio.run(Runner.run(
        zoom_cars_agent,
        "First identify what does the customer want - Vehicle Register/Complaint Register. Then ask the questions one by one.",
        session=session
    ))
    return jsonify({"reply": result.final_output})


@app.route("/chat", methods=["POST"])
def chat():
    """Continue conversation based on user response"""
    user_input = request.json.get("message")

    # Run agent
    result = asyncio.run(Runner.run(
        zoom_cars_agent,
        user_input,
        session=session
    ))
    return jsonify({"reply": result.final_output})


@app.route("/end", methods=["GET"])
def end():
    """End the session"""
    session.close()
    return jsonify({"reply": "Session closed successfully."})


if __name__ == "__main__":
    app.run(debug=True)
