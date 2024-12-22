// Technical service functionality
class TechnicalService {
    constructor() {
        this.serviceRequests = [];
    }
    
    submitRequest(request) {
        this.serviceRequests.push(request);
    }
}