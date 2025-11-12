"""
Vision tool for processing image inputs (Part 4 requirement).
Uses Groq's vision capabilities to analyze screenshots and extract information.
"""

import base64
from typing import Dict, Any, Optional
import httpx
import os
from backend.mcp.orchestration import SupabaseOrchestrator


class VisionTool:
    """
    Vision tool for processing image inputs.
    Analyzes screenshots to extract trip information, UI elements, etc.
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.orchestrator = SupabaseOrchestrator()
    
    def process_image(
        self,
        image_base64: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Process an image with a user query using Groq's vision model.
        
        Args:
            image_base64: Base64 encoded image
            user_query: User's query about the image
            
        Returns:
            Dict with extracted information and suggested actions
        """
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for vision processing")
        
        # Prepare vision prompt
        vision_prompt = f"""You are analyzing a screenshot of a transport management system dashboard.
The user said: "{user_query}"

Please analyze the image and:
1. Identify any trips, routes, vehicles, or drivers mentioned or visible
2. Extract any trip names, route names, vehicle license plates, or driver names
3. Identify what action the user wants to perform (if any)
4. Return a JSON object with:
   - trip_names: List of trip names found (e.g., ["Bulk - 00:01"])
   - route_names: List of route names found
   - vehicle_plates: List of vehicle license plates found
   - driver_names: List of driver names found
   - suggested_action: The action the user wants (e.g., "remove_vehicle", "assign_vehicle", "delete_trip")
   - target_entity: The specific entity to act on (trip name, route name, etc.)

Return ONLY valid JSON, no other text."""

        try:
            # Call Groq API with vision
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.groq_api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.groq_api_key}"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",  # Groq vision-capable model
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": vision_prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", str(error_data))
                    except:
                        error_detail = response.text
                    raise Exception(f"Vision API error {response.status_code}: {error_detail}")
                
                data = response.json()
                vision_response = data["choices"][0]["message"]["content"]
                
                # Try to parse JSON from response
                import json
                import re
                
                # Extract JSON from response (might have markdown code blocks)
                json_match = re.search(r'\{.*\}', vision_response, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    # Fallback: try to parse entire response
                    extracted_data = json.loads(vision_response)
                
                return {
                    "success": True,
                    "extracted_data": extracted_data,
                    "raw_response": vision_response
                }
                
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            return {
                "success": True,
                "extracted_data": {
                    "suggested_action": "unknown",
                    "raw_analysis": vision_response
                },
                "raw_response": vision_response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extracted_data": {}
            }
    
    def match_entities_from_vision(
        self,
        vision_result: Dict[str, Any],
        state: str
    ) -> Dict[str, Any]:
        """
        Match extracted entities from vision with database records.
        
        Args:
            vision_result: Result from process_image
            state: Current state (route_management or bus_dashboard)
            
        Returns:
            Dict with matched entities and suggested tool calls
        """
        if not vision_result.get("success"):
            return vision_result
        
        extracted = vision_result.get("extracted_data", {})
        matched_entities = {
            "trips": [],
            "routes": [],
            "vehicles": [],
            "drivers": []
        }
        
        # Match trips
        trip_names = extracted.get("trip_names", [])
        if trip_names:
            all_trips = self.orchestrator.get_trips()
            for trip_name in trip_names:
                # Try to find matching trip
                for trip in all_trips:
                    if trip_name.lower() in trip.get("display_name", "").lower():
                        matched_entities["trips"].append(trip)
                        break
        
        # Match routes
        route_names = extracted.get("route_names", [])
        if route_names:
            all_routes = self.orchestrator.get_routes()
            for route_name in route_names:
                for route in all_routes:
                    if route_name.lower() in route.get("route_display_name", "").lower():
                        matched_entities["routes"].append(route)
                        break
        
        # Match vehicles
        vehicle_plates = extracted.get("vehicle_plates", [])
        if vehicle_plates:
            all_vehicles = self.orchestrator.get_vehicles()
            for plate in vehicle_plates:
                for vehicle in all_vehicles:
                    if plate.lower() in vehicle.get("license_plate", "").lower():
                        matched_entities["vehicles"].append(vehicle)
                        break
        
        # Match drivers
        driver_names = extracted.get("driver_names", [])
        if driver_names:
            all_drivers = self.orchestrator.get_drivers()
            for name in driver_names:
                for driver in all_drivers:
                    if name.lower() in driver.get("name", "").lower():
                        matched_entities["drivers"].append(driver)
                        break
        
        return {
            "success": True,
            "extracted_data": extracted,
            "matched_entities": matched_entities,
            "suggested_action": extracted.get("suggested_action"),
            "target_entity": extracted.get("target_entity")
        }

