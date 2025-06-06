// This file adds debugging functionality to help fix dashboard data issues

// Function to check what's in localStorage
function debugLocalStorage() {
    console.log("==== DEBUG LOCAL STORAGE ====");
    
    // Check all relevant localStorage keys
    console.log("sourcesFormState:", localStorage.getItem('sourcesFormState'));
    console.log("sourcesData:", localStorage.getItem('sourcesData'));
    
    // Parse sourcesFormState if it exists
    const formState = localStorage.getItem('sourcesFormState');
    if (formState) {
        try {
            const parsedState = JSON.parse(formState);
            console.log("Parsed sourcesFormState:", parsedState);
            if (parsedState.selectedSources) {
                console.log("Selected sources:", parsedState.selectedSources);
            } else {
                console.log("No selectedSources found in parsed state");
            }
        } catch (error) {
            console.error("Error parsing sourcesFormState:", error);
        }
    }
    
    console.log("==== END DEBUG ====");
}

// Function to set default sources
function setDefaultSources() {
    const defaultSources = ['arxiv', 'techcrunch', 'theverge'];
    const state = {
        selectedSources: defaultSources,
        arxivCategory: 'cs.LG',
        maxArticles: 10,
        citationStyles: ['apa'],
        timestamp: new Date().getTime()
    };
    
    localStorage.setItem('sourcesFormState', JSON.stringify(state));
    console.log("Default sources set:", defaultSources);
    console.log("Refresh the page to use these sources");
}

// Function to debug the endpoints
async function testEndpoints() {
    console.log("==== TESTING ENDPOINTS ====");
    
    // Test sources
    const testSources = ['arxiv', 'techcrunch', 'theverge'];
    
    // Test /api/fetch_data endpoint
    try {
        console.log("Testing /api/fetch_data endpoint...");
        const fetchDataResponse = await fetch('/api/fetch_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sources: testSources,
                arxiv_category: 'cs.LG',
                max_articles: 10,
                citation_styles: ['apa']
            })
        });
        
        console.log(`/api/fetch_data status: ${fetchDataResponse.status}`);
        if (fetchDataResponse.ok) {
            console.log("Endpoint working!");
        } else {
            console.log("Endpoint failed!");
            const errorText = await fetchDataResponse.text();
            console.log("Error text:", errorText);
        }
    } catch (error) {
        console.error("/api/fetch_data test failed:", error);
    }
    
    // Test /get-data endpoint
    try {
        console.log("\nTesting /get-data endpoint...");
        const getDataResponse = await fetch('/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sources: testSources
            })
        });
        
        console.log(`/get-data status: ${getDataResponse.status}`);
        if (getDataResponse.ok) {
            console.log("Endpoint working!");
        } else {
            console.log("Endpoint failed!");
            const errorText = await getDataResponse.text();
            console.log("Error text:", errorText);
        }
    } catch (error) {
        console.error("/get-data test failed:", error);
    }
    
    console.log("==== END TESTING ====");
}

// Add these to window for console access
window.debugLocalStorage = debugLocalStorage;
window.setDefaultSources = setDefaultSources;
window.testEndpoints = testEndpoints;

console.log("Dashboard debugging tools loaded. Available commands:");
console.log("- debugLocalStorage() - Inspect localStorage contents");
console.log("- setDefaultSources() - Set default sources in localStorage");
console.log("- testEndpoints() - Test API endpoints");
