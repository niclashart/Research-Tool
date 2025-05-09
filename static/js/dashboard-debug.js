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
    alert("Default sources set! Refresh the page to use these sources.");
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
            const data = await fetchDataResponse.json();
            console.log("Data received:", data);
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
            const data = await getDataResponse.json();
            console.log("Data received:", data);
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

// Helper UI for debugging
function addDebugUI() {
    // Create a debug panel
    const debugPanel = document.createElement('div');
    debugPanel.style.position = 'fixed';
    debugPanel.style.bottom = '10px';
    debugPanel.style.left = '10px';
    debugPanel.style.zIndex = '9999';
    debugPanel.style.backgroundColor = 'rgba(0,0,0,0.7)';
    debugPanel.style.padding = '10px';
    debugPanel.style.borderRadius = '5px';
    debugPanel.style.color = 'white';
    debugPanel.style.fontSize = '12px';
    debugPanel.style.fontFamily = 'monospace';
    
    // Add buttons
    debugPanel.innerHTML = `
        <div style="margin-bottom:5px;">Dashboard Debug Tools</div>
        <button id="debug-ls" style="background:#444;color:white;border:none;padding:3px 6px;margin:2px;border-radius:3px;">Debug LocalStorage</button>
        <button id="set-default" style="background:#444;color:white;border:none;padding:3px 6px;margin:2px;border-radius:3px;">Set Default Sources</button>
        <button id="test-endpoints" style="background:#444;color:white;border:none;padding:3px 6px;margin:2px;border-radius:3px;">Test Endpoints</button>
        <button id="hide-debug" style="background:#666;color:white;border:none;padding:3px 6px;margin:2px;border-radius:3px;">Hide</button>
    `;
    
    // Add to body
    document.body.appendChild(debugPanel);
    
    // Add event listeners
    document.getElementById('debug-ls').addEventListener('click', debugLocalStorage);
    document.getElementById('set-default').addEventListener('click', setDefaultSources);
    document.getElementById('test-endpoints').addEventListener('click', testEndpoints);
    document.getElementById('hide-debug').addEventListener('click', () => {
        debugPanel.style.display = 'none';
    });
}

// Add debug UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addDebugUI, 1000);
    console.log("Dashboard debugging tools loaded. Available commands:");
    console.log("- debugLocalStorage() - Inspect localStorage contents");
    console.log("- setDefaultSources() - Set default sources in localStorage");
    console.log("- testEndpoints() - Test API endpoints");
});
