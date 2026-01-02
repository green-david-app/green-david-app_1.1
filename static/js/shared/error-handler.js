// ============================================
// CENTRALIZED ERROR HANDLER
// ============================================

/**
 * Error types
 */
const ErrorTypes = {
    NETWORK: 'network',
    TIMEOUT: 'timeout',
    VALIDATION: 'validation',
    PERMISSION: 'permission',
    NOT_FOUND: 'not_found',
    SERVER: 'server',
    UNKNOWN: 'unknown'
};

/**
 * Error messages (Czech)
 */
const ErrorMessages = {
    [ErrorTypes.NETWORK]: 'Problém s připojením k internetu',
    [ErrorTypes.TIMEOUT]: 'Požadavek trval příliš dlouho',
    [ErrorTypes.VALIDATION]: 'Neplatná data ve formuláři',
    [ErrorTypes.PERMISSION]: 'Nemáte oprávnění k této akci',
    [ErrorTypes.NOT_FOUND]: 'Požadovaná položka nebyla nalezena',
    [ErrorTypes.SERVER]: 'Chyba serveru. Zkuste to později.',
    [ErrorTypes.UNKNOWN]: 'Něco se pokazilo. Zkuste to znovu.'
};

/**
 * Classify error type
 */
function classifyError(error) {
    // Network offline
    if (!navigator.onLine) {
        return ErrorTypes.NETWORK;
    }
    
    // Timeout
    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
        return ErrorTypes.TIMEOUT;
    }
    
    // HTTP status codes
    if (error.status) {
        if (error.status === 404) return ErrorTypes.NOT_FOUND;
        if (error.status === 403 || error.status === 401) return ErrorTypes.PERMISSION;
        if (error.status >= 500) return ErrorTypes.SERVER;
        if (error.status >= 400) return ErrorTypes.VALIDATION;
    }
    
    // Validation errors
    if (error.message && error.message.includes('invalid')) {
        return ErrorTypes.VALIDATION;
    }
    
    return ErrorTypes.UNKNOWN;
}

/**
 * Get user-friendly error message
 */
function getErrorMessage(error) {
    const type = classifyError(error);
    
    // Use custom message if available
    if (error.userMessage) {
        return error.userMessage;
    }
    
    // Use default message for type
    return ErrorMessages[type] || ErrorMessages[ErrorTypes.UNKNOWN];
}

/**
 * Handle error globally
 */
function handleError(error, context = '') {
    const message = getErrorMessage(error);
    const type = classifyError(error);
    
    // Log to console (for developers)
    console.group(`❌ Error in ${context || 'App'}`);
    console.error('Type:', type);
    console.error('Message:', message);
    console.error('Original error:', error);
    console.groupEnd();
    
    // Show user-friendly message
    const toastType = type === ErrorTypes.VALIDATION ? 'warning' : 'error';
    if (typeof window.showToast === 'function') {
        window.showToast(message, toastType);
    } else {
        console.error('showToast not available:', message);
    }
    
    // Send to error tracking (optional)
    if (window.Sentry) {
        window.Sentry.captureException(error, {
            tags: { context, type }
        });
    }
    
    // Return for further handling
    return {
        type,
        message,
        originalError: error
    };
}

/**
 * Retry function with exponential backoff
 */
async function retryWithBackoff(fn, maxRetries = 3, delayMs = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            
            const delay = delayMs * Math.pow(2, i);
            console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}

/**
 * Safe async wrapper
 */
async function tryCatch(fn, context = '') {
    try {
        return await fn();
    } catch (error) {
        return handleError(error, context);
    }
}

// Export
window.ErrorHandler = {
    ErrorTypes,
    classifyError,
    getErrorMessage,
    handleError,
    retryWithBackoff,
    tryCatch
};

