from django.shortcuts import render

# Create your views here.
# @app.post("/chat/completion")
# async def openai_streaming(request: InferenceRequest, provider: str = Query(None, description="Name of the LLM Provider")) -> StreamingResponse:
#     # Extract request data
#     messages = request.messages
#     model_name = request.model_name

#     # Initialize and load model
#     llm = LLM_Factory(provider)
#     llm.api_key = "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"  # Set the API key
#     await llm.load_model(model_name)

#     try:
#         # Generate streaming response
#         subscription = llm.chat(messages)
#         return StreamingResponse(subscription, media_type='text/event-stream')
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error in chat completion: {str(e)}")