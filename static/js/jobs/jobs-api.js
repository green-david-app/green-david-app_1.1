// ============================================
// JOBS API CLIENT WITH COMPREHENSIVE ERROR HANDLING
// ============================================

/**
 * Enhanced API wrapper with comprehensive error handling
 */
async function apiCall(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    try {
        // Check online status first
        if (!navigator.onLine) {
            throw new Error('Offline');
        }
        
        // Make request
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            signal: controller.signal
        });
        
        // Clear timeout
        clearTimeout(timeoutId);
        
        // Handle HTTP errors
        if (!response.ok) {
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                // Response is not JSON
            }
            
            const error = new Error(errorData.message || errorData.error || `HTTP ${response.status}`);
            error.status = response.status;
            error.data = errorData;
            
            // Add user-friendly message
            if (response.status === 404) {
                error.userMessage = 'Položka nebyla nalezena';
            } else if (response.status === 403) {
                error.userMessage = 'Nemáte oprávnění k této akci';
            } else if (response.status >= 500) {
                error.userMessage = 'Chyba serveru. Zkuste to za chvíli.';
            } else if (response.status === 400) {
                error.userMessage = errorData.message || errorData.error || 'Neplatná data';
            }
            
            throw error;
        }
        
        // Parse response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        // Handle specific error types
        if (error.name === 'AbortError') {
            const timeoutError = new Error('Request timeout');
            timeoutError.name = 'TimeoutError';
            throw timeoutError;
        }
        
        if (!navigator.onLine || error.message === 'Offline') {
            const offlineError = new Error('No internet connection');
            offlineError.userMessage = 'Zkontrolujte připojení k internetu';
            throw offlineError;
        }
        
        throw error;
    }
}

/**
 * Fetch jobs with error handling
 */
async function fetchJobs() {
    try {
        if (typeof showLoadingOverlay === 'function') {
            showLoadingOverlay('Načítám zakázky...');
        }
        
        const data = await apiCall('/api/jobs');
        
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        
        return data;
        
    } catch (error) {
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (window.ErrorHandler) {
            window.ErrorHandler.handleError(error, 'fetchJobs');
        }
        throw error;
    }
}

/**
 * Create job with validation and error handling
 */
async function createJob(jobData) {
    try {
        if (typeof showLoadingOverlay === 'function') {
            showLoadingOverlay('Vytvářím zakázku...');
        }
        
        // Validate data first
        if (!jobData.title || !jobData.title.trim()) {
            const validationError = new Error('Název zakázky je povinný');
            validationError.userMessage = 'Vyplňte název zakázky';
            throw validationError;
        }
        
        const data = await apiCall('/api/jobs', {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
        
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (typeof window.showToast === 'function') {
            window.showToast('Zakázka vytvořena', 'success');
        }
        return data;
        
    } catch (error) {
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (window.ErrorHandler) {
            window.ErrorHandler.handleError(error, 'createJob');
        }
        throw error;
    }
}

/**
 * Update job with error handling
 */
async function updateJob(jobId, jobData) {
    try {
        if (typeof showLoadingOverlay === 'function') {
            showLoadingOverlay('Ukládám změny...');
        }
        
        const data = await apiCall('/api/jobs', {
            method: 'PATCH',
            body: JSON.stringify({ id: jobId, ...jobData })
        });
        
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (typeof window.showToast === 'function') {
            window.showToast('Změny uloženy', 'success');
        }
        return data;
        
    } catch (error) {
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (window.ErrorHandler) {
            window.ErrorHandler.handleError(error, 'updateJob');
        }
        throw error;
    }
}

/**
 * Delete job with error handling
 */
async function deleteJob(jobId) {
    try {
        if (typeof showLoadingOverlay === 'function') {
            showLoadingOverlay('Mažu zakázku...');
        }
        
        await apiCall(`/api/jobs?id=${jobId}`, {
            method: 'DELETE'
        });
        
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (typeof window.showToast === 'function') {
            window.showToast('Zakázka smazána', 'success');
        }
        
    } catch (error) {
        if (typeof hideLoadingOverlay === 'function') {
            hideLoadingOverlay();
        }
        if (window.ErrorHandler) {
            window.ErrorHandler.handleError(error, 'deleteJob');
        }
        throw error;
    }
}

/**
 * Retry decorator pro nestabilní operace
 */
async function updateJobWithRetry(jobId, jobData) {
    if (!window.ErrorHandler) {
        return updateJob(jobId, jobData);
    }
    
    return await window.ErrorHandler.retryWithBackoff(
        () => updateJob(jobId, jobData),
        3, // max 3 retries
        1000 // start with 1s delay
    );
}

// Export
window.JobsAPI = {
    fetchJobs,
    createJob,
    updateJob,
    deleteJob,
    updateJobWithRetry,
    apiCall
};

