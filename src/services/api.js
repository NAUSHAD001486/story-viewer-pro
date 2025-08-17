// src/services/api.js

const API_BASE_URL = 'https://x7c8htbkjf.execute-api.ap-south-1.amazonaws.com'; // Yeh aapka live URL hai
let apiToken = null;

// API se naya JWT token fetch karne ka function
async function getApiToken() {
  const response = await fetch(`${API_BASE_URL}/v1/auth/token`, { method: 'POST' });
  if (!response.ok) throw new Error('API se authenticate nahi kar paaye.');
  const data = await response.json();
  return data.token;
}

// Token ko manage karne ka function
async function ensureApiToken() {
    if (!apiToken) {
        console.log("Naya API token fetch kar rahe hain...");
        apiToken = await getApiToken();
    }
    return apiToken;
}

// Profile data fetch karne wala function
export async function fetchInstagramData(username) { // Ab yeh poora URL nahi, sirf username lega
  try {
    const token = await ensureApiToken();
    
    // Username ko URL me istemal ke liye encode karein
    const encodedUsername = encodeURIComponent(username);
    const requestUrl = `${API_BASE_URL}/v1/profile?url=${encodedUsername}`; // Hum 'url' parameter me hi username bhej rahe hain

    const response = await fetch(requestUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.status === 401 || response.status === 403) {
        console.log("Token expire ho gaya, naya fetch kar rahe hain.");
        apiToken = null;
        return fetchInstagramData(username); // Naye token ke saath dobara try karein
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Request fail ho gaya: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API se fetch karne me error:', error);
    throw new Error('Profile fetch nahi kar paaye.');
  }
}

// Content (Reel/Post) fetch karne wala function
export async function fetchInstagramContent(contentUrl) {
  try {
    const token = await ensureApiToken();
    const encodedUrl = encodeURIComponent(contentUrl);
    const requestUrl = `${API_BASE_URL}/v1/content?url=${encodedUrl}`;

    const response = await fetch(requestUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (response.status === 401 || response.status === 403) {
        apiToken = null;
        return fetchInstagramContent(contentUrl);
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Request failed: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching content from API:', error);
    throw new Error('Could not fetch the requested content.');
  }
}