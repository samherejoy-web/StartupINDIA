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
  - task: "Implement XPath-based data extraction with BeautifulSoup fallback"
    implemented: true
    working: "needs_testing"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "needs_testing"
        agent: "main"
        comment: |
          UPDATED: Added BeautifulSoup fallback mechanism after Playwright installation.
          
          Implementation includes:
          1. Installed Playwright chromium browser (167.3 MB)
          2. Created scrape_with_beautifulsoup() function as fallback
          3. Modified scrape_startup_india_page() to try Playwright first, then BeautifulSoup if it fails
          4. BeautifulSoup fallback uses CSS selectors to mimic XPath behavior
          5. Both methods include regex fallback for critical fields
          
          Scraping Strategy:
          - Primary: Playwright with XPath selectors (best for JavaScript-rendered content)
          - Secondary: BeautifulSoup with CSS selectors (faster, works for static HTML)
          - Tertiary: Regex pattern matching (catches edge cases)
          
          This ensures high reliability and data extraction success rate.
  
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
      IMPLEMENTATION COMPLETE - XPath-based crawler with BeautifulSoup fallback:
      
      ## Changes Made:
      
      1. **Playwright Browser Installation**:
         - Installed chromium browser for Playwright (167.3 MB)
         - Browser path: /pw-browsers/chromium-1208/chrome-linux64/chrome
         - Ready for JavaScript-rendered content scraping
      
      2. **Three-Tier Scraping Strategy**:
         
         **Tier 1: Playwright with XPath** (Primary, lines 108-304)
         - Uses specific XPath selectors for all 15 fields
         - Best for JavaScript-rendered pages like Startup India portal
         - Waits 12 seconds for content to render
         - Includes error handling per field
         
         **Tier 2: BeautifulSoup Fallback** (Secondary, lines 89-107)
         - Activates if Playwright fails (browser issues, timeouts, etc.)
         - Uses CSS selectors to mimic XPath behavior
         - Faster execution for static HTML
         - Includes same field validation and filtering
         
         **Tier 3: Regex Fallback** (Tertiary, in both methods)
         - Extracts critical fields (name, email, website) from raw text
         - Catches edge cases where DOM structure differs
         - Pattern matching for company names, emails, phone numbers
      
      3. **XPath Fields Implemented**:
         ✓ name: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/p
         ✓ website: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[3]/a
         ✓ email: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[2]
         ✓ contact_number: //*[@id="txtEditor"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/span[1]
         ✓ mobile_number: (same as contact_number)
         ✓ stage: //*[@id="1638164275868262-0"]/.../span[1]/span[2]
         ✓ focus_industry: //*[@id="1638164275868262-0"]/.../span[2]/span[2]
         ✓ focus_sector: //*[@id="1638164275868262-0"]/.../span[3]/span[2]
         ✓ service_area: //*[@id="1638164275868262-0"]/.../span[4]/span[2]
         ✓ location: //*[@id="1638164275868262-0"]/.../span[5]/span[2]
         ✓ active_years: //*[@id="1638164275868262-0"]/.../span[6]/span[2]/p
         ✓ engagement_level: //*[@id="txtEditor"]/.../h6[1]/span/strong
         ✓ active_on_portal: (same as engagement_level)
         ✓ about_company: //*[@id="1638164275868262-0"]/.../div[1]/div/div[1]
         ✓ domain: (auto-extracted from website URL)
      
      4. **Enhanced Features**:
         - Automatic domain extraction from website URLs
         - Invalid value filtering (×, —, N/A, XXXXXXX, 0000000000)
         - Comprehensive logging for debugging
         - Website crawling when website URL is found
         - Proper error handling at each extraction level
      
      5. **Website Crawling** (lines 306-357):
         - Async Playwright-based website scraping
         - Extracts: about_company, email, contact info, location
         - 3-second wait for page rendering
         - Filters out fake/placeholder data
      
      ## Testing Instructions:
      
      **Test Scenario 1: Single URL Scraping**
      ```bash
      curl -X POST http://localhost:8001/api/scrape \
        -H "Content-Type: application/json" \
        -d '{"url": "https://www.startupindia.gov.in/content/sih/en/startupgov/startup-profile/[STARTUP_ID].html"}'
      ```
      
      **Test Scenario 2: Bulk URL Scraping**
      ```bash
      curl -X POST http://localhost:8001/api/scrape/bulk \
        -H "Content-Type: application/json" \
        -d '{"urls": ["URL1", "URL2", "URL3"]}'
      ```
      
      **Test Scenario 3: Check Saved Data**
      ```bash
      curl http://localhost:8001/api/scraped-data
      ```
      
      ## What to Verify:
      
      1. ✓ All 15 fields are extracted when available
      2. ✓ Playwright extraction works (check logs for "Playwright extracted")
      3. ✓ BeautifulSoup fallback activates if Playwright fails
      4. ✓ Website crawling happens when website URL is found
      5. ✓ Data is saved to MongoDB correctly
      6. ✓ Invalid values are filtered out
      7. ✓ Domain is automatically extracted from website
      8. ✓ Error handling works for invalid URLs
      
      ## Expected Log Messages:
      - "Navigating to URL with Playwright: [URL]"
      - "Extracted [field]: [value]" (for each field found)
      - "Playwright extracted X fields successfully"
      - OR "Falling back to BeautifulSoup scraping..." (if Playwright fails)
      - "Website found: [URL], crawling for additional details..."
      - "Successfully saved scraped data for [URL]"
      
      Backend is running and ready for testing at http://localhost:8001
      
      **IMPORTANT**: Please provide actual Startup India portal URLs to test with, as the scraper is specifically designed for that portal's structure.