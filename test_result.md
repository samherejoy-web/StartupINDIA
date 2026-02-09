#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Fix crawler functionality to extract accurate results from Startup India portal pages using specific XPath selectors, and ensure website crawling works correctly when websites are found."

backend:
  - task: "Implement XPath-based data extraction"
    implemented: true
    working: "needs_testing"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "needs_testing"
        agent: "main"
        comment: "Replaced generic CSS selectors and regex patterns with specific XPath selectors for all fields (name, domain, website, email, contact_number, mobile_number, stage, focus_industry, focus_sector, service_area, location, active_years, engagement_level, active_on_portal, about_company). Added fallback mechanism for critical fields if XPath extraction fails."
  
  - task: "Website crawling for additional details"
    implemented: true
    working: "needs_testing"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "needs_testing"
        agent: "main"
        comment: "Enhanced scrape_website_details function to use Playwright for better JavaScript support. Now properly extracts about_company, email, phone numbers, and location from company websites. Made it async to work properly with the main scraping flow."

frontend:
  - task: "No frontend changes required"
    implemented: true
    working: true
    file: "N/A"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Frontend already has the UI for displaying scraped data. No changes needed for this task."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Implement XPath-based data extraction"
    - "Website crawling for additional details"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      IMPLEMENTATION COMPLETE - XPath-based crawler fixes:
      
      ## Changes Made:
      
      1. **XPath-Based Data Extraction** (server.py lines 108-220):
         - Implemented specific XPath selectors for all 15 fields:
           * name: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/p
           * website: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[3]/a
           * email: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[2]
           * contact_number: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[1]
           * stage: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[1]/span[2]
           * focus_industry: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[2]/span[2]
           * focus_sector: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[3]/span[2]
           * service_area: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[4]/span[2]
           * location: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[5]/span[2]
           * active_years: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[2]/div/div/div/div/span[6]/span[2]/p
           * engagement_level: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/h6[1]/span/strong
           * about_company: //*[@id="1638164275868262-0"]/div/div/div/div/div/div/div[1]/div/div[1]
         
         - Used Playwright's locator API with xpath prefix for precise element selection
         - Added proper error handling for each field extraction
         - Implemented value filtering to exclude invalid entries (×, —, N/A, XXXXXXX, etc.)
         - Special handling for duplicate XPaths (mobile_number, active_on_portal)
         - Automatic domain extraction from website URLs
      
      2. **Fallback Mechanism** (server.py lines 195-218):
         - If XPath extraction fails for critical fields (name, email, website)
         - Falls back to regex pattern matching on page text
         - Ensures at least basic data is captured even if page structure changes
      
      3. **Enhanced Website Crawling** (server.py lines 358-405):
         - Converted to async function using Playwright instead of requests
         - Better JavaScript support for dynamic websites
         - Extracts: about_company, email, contact numbers, location
         - Proper error handling and timeout management
         - Filters out invalid/fake contact information
      
      4. **Improved Main Scraping Flow** (server.py lines 407-442):
         - Fixed async/await for website scraping
         - Proper data merging (prefers Startup India data over website data)
         - Enhanced logging for debugging
         - Better error tracking and status reporting
      
      ## Testing Instructions:
      
      Please test the following scenarios:
      
      1. **Single URL Scraping**:
         - POST to /api/scrape with a Startup India portal URL
         - Verify all fields are extracted correctly using XPaths
         - Check if website is crawled when found
         - Verify data is saved to MongoDB
      
      2. **Bulk URL Scraping**:
         - POST to /api/scrape/bulk with multiple URLs
         - Verify rate limiting is working (1 second delay between requests)
         - Check all URLs are processed successfully
      
      3. **Website Crawling**:
         - When a website URL is found in Startup India data
         - Verify the website is crawled for additional details
         - Check about_company field is populated
         - Verify additional contact info is extracted
      
      4. **Error Handling**:
         - Test with invalid URLs
         - Test with pages that don't match XPath structure
         - Verify fallback mechanism works
         - Check error messages are logged properly
      
      ## Expected Behavior:
      - XPath selectors should extract data more accurately than before
      - All 15 fields should be extracted when available on the page
      - Website crawling should work automatically when website URL is found
      - Data should be stored in MongoDB with proper structure
      - Invalid/placeholder values should be filtered out
      
      Backend is running and ready for testing.