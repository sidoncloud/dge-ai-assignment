import os
import logging
from dotenv import load_dotenv, find_dotenv
import openai
from flask import Flask, request, jsonify
from langgraph.prebuilt import create_react_agent
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain, load_summarize_chain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.document_loaders import UnstructuredExcelLoader, PyPDFLoader
from langgraph_supervisor import create_supervisor
from langchain_core.vectorstores import InMemoryVectorStore

# Configure logging to debug agent inputs and outputs
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(find_dotenv(), override=True)

# API key
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# Embeddings and LLM setup
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
llm_openai = ChatOpenAI(model="gpt-4-turbo-2024-04-09", api_key=api_key, temperature=0.1)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')

# Credit policy vector store
credit_policy_vector_store = Chroma(
    collection_name="credit_policy_collection",
    embedding_function=embeddings,
    persist_directory="./chroma1_db",
)

def credit_risk_evaluation(emirates_id: str) -> str:
    """
    Evaluates the credit risk of the applicant.

    Loads the PDF at credit-reports/{emirates_id}.pdf, summarizes it,
    then performs a semantic search over credit_policy_vector_store
    to determine compliance.

    Args:
        emirates_id (str): The Emirates ID number to locate the PDF.

    Returns:
        str: JSON string with credit risk evaluation.
    """
    logger.debug(f"[credit_risk_evaluation] called with ID: {emirates_id}")
    pdf_path = f"credit-reports/{emirates_id}.pdf"
    loader = PyPDFLoader(pdf_path)
    docs = loader.load_and_split()
    summary = load_summarize_chain(llm_openai, chain_type="stuff", verbose=False).invoke(docs)
    final_summary = summary['output_text']

    query = (
        "Given the below summary of the credit report of an applicant, "
        "check whether the applicant is eligible for financial support given the credit policy rules.\n"
        f"Credit report Summary:\n{final_summary}"
    )

    retriever = credit_policy_vector_store.as_retriever(search_type="mmr", search_kwargs={"k":1, "fetch_k":2})
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm_openai, retriever=retriever, memory=memory, verbose=False
    )
    result = conv_chain.invoke(query)["answer"]
    logger.debug(f"[credit_risk_evaluation] result: {result}")
    return result

credit_risk_evaluator_agent = create_react_agent(
    model=llm_openai,
    tools=[credit_risk_evaluation],
    prompt=(
        "You are a Credit Risk Evaluation Agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Your job is to assess whether the applicant's credit report violates any financial support policies.\n"
        "- Use the available tools to retrieve and analyze relevant credit policy documents.\n"
        "- Extract matching policies or clauses using semantic search and base your evaluation on those.\n"
        "- Respond with ONLY the compliance result, the matched policies, and your risk assessment.\n"
        "- DO NOT explain your reasoning or add extra commentary.\n"
        "- Once your analysis is complete, send the structured result back to the supervisor.\n\n"
        "Your final output must only contain the following attributes:\n"
        "  credit_risk: \"High\" or \"Low\",\n"
        "  policy_matches: [\"DTI >=<number>\"],\n"
        "  compliance_flag: true or false"
    ),
    name="credit_risk_evaluator"
)


def summarize_bank_statements(emirates_id: str) -> str:
    """
    Summarizes the bank statements to extract the contributing factors.

    Args:
        emirates_id (str): The Emirates ID number to locate the XLSX.

    Returns:
        str: A brief text summary of financial transactions.
    """
    query = (
        "Summarize the bank statement with key points and not more than 400 characters "
        "highlighting the key factors that will contribute to the applicant's economic support plan."
    )
    xls_path = f"bank-statements/{emirates_id}.xlsx"
    loader = UnstructuredExcelLoader(xls_path)
    docs = loader.load()
    store = InMemoryVectorStore(embeddings)
    store.add_documents(documents=docs)
    retriever = store.as_retriever(search_type="mmr", search_kwargs={"k":1, "fetch_k":2, "lambda_mult":0.5})
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm_openai, retriever=retriever, memory=memory, verbose=False
    )
    result = conv_chain.invoke(query)["answer"]
    logger.debug(f"[summarize_bank_statements] result: {result}")
    return result

financial_burden_agent = create_react_agent(
    model=llm_openai,
    tools=[summarize_bank_statements],
    prompt=(
        "You are a Financial Hardship Assessment Agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Your job is to calculate the applicant’s true financial hardship based on their income, liabilities, and number of dependents.\n"
        "- Use the available tools to retrieve and summarize the applicant’s bank statements, loan obligations, and dependent count.\n"
        "- Compute key metrics: debt-to-income ratio, monthly disposable income after liabilities, and per-dependent allocation.\n"
        "- Respond with ONLY a JSON object containing these metrics and an overall hardship classification (High, Moderate, Low).\n"
        "- Your final JSON must include exactly the following fields:\n"
        "  net_worth,\n"
        "  debt_to_income,\n"
        "  burden_score\n"
        "- Do NOT include any other keys, explanations, or commentary.\n"
        "- Return the structured result back to the supervisor when complete."
    ),
    name="financial_burden_evaluator"
)

social_support_supervisor = create_supervisor(
    model=llm_openai,
    agents=[financial_burden_agent, credit_risk_evaluator_agent],
    prompt=(
        "You are the Social Support Application Supervisor.\n"
        "Manage two agents:\n"
        "- financial_burden_agent: calculates true financial hardship and returns JSON with net_worth, debt_to_income, burden_score.\n"
        "- credit_risk_evaluator_agent: evaluates credit risk and returns JSON with credit_risk, policy_matches, compliance_flag.\n\n"
        "When a user query arrives:\n"
        "  1. Delegate to the appropriate agent (only one agent per request).\n"
        "  2. After you receive that agent’s output, use both sets of attributes to derive the final recommendation.\n\n"
        "Final decision logic examples:\n"
        "- If credit_risk is \"Low\" AND debt_to_income < 0.5 AND burden_score < 0.5 AND compliance_flag is true → Approved\n"
        "- If credit_risk is \"High\" OR debt_to_income > 0.8 OR burden_score > 0.8 OR compliance_flag is false → Soft Decline\n"
        "- Otherwise → Approved with Conditions\n\n"
        "Respond with ONLY a JSON object containing:\n"
        "  financial_support_decision: \"Approved\" | \"Soft Decline\" | \"Approved with Conditions\",\n"
        "  reason: a brief phrase like \"Low burden and acceptable credit\" or \"High debt-to-income ratio\""
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()

# Flask app
app = Flask(__name__)

@app.route('/evaluate', methods=['POST'])
def evaluate():
    """
    HTTP POST endpoint to process an applicant’s data.

    Expects JSON:
      {
        "emirates_id": "<string>",
        "applicant_data": { ... }
      }

    Returns:
      JSON: {"result": <decision JSON>} or {"error": "..."}
    """
    data = request.get_json()
    logger.debug(f"[evaluate] Received payload: {data}")
    emirates_id = data.get('emirates_id')
    applicant_data = data.get('applicant_data')
    if not emirates_id or not applicant_data:
        logger.error("[evaluate] Missing emirates_id or applicant_data in payload")
        return jsonify({'error': 'Missing emirates_id or applicant_data'}), 400

    query = f"Applicant Emirates ID: {emirates_id}. Here is their data: {applicant_data}."
    logger.debug(f"[evaluate] Supervisor query: {query}")
    try:
        response = social_support_supervisor.invoke(
            {"messages": [{"role": "user", "content": query}]},
            {"recursion_limit": 10}
        )
        logger.debug(f"[evaluate] Supervisor raw response: {response}")
        history = response.get("messages", [])
        last_msg = history[-1] if history else {}
        final = last_msg.content if hasattr(last_msg, 'content') else last_msg.get('content')
        logger.debug(f"[evaluate] Final decision: {final}")
        return jsonify({'result': final})
    except Exception as e:
        logger.exception("[evaluate] Error during supervisor invocation")
        return jsonify({'error': 'Internal processing error'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)