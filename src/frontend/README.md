# Frontend

This is the frontend application for the on-premises RAG system.

## Features

### Query Interface

- **Search Functionality**: Users can search through uploaded documents using natural language queries
- **Real-time Feedback**:
  - Loading indicators during search operations
  - Clear error messages when API calls fail
  - Informative messages when no results are found
  - Result count display when documents are found
- **Parameter Configuration**: Users can select different RAG parameter sets for optimized search results
- **Result Selection**: Click on search results to view document content in the appropriate viewer

### Document Viewers

- **PDF Viewer**: Displays PDF documents with page navigation
- **DOCX Viewer**: Shows Word documents with formatting preserved
- **Text Viewer**: Displays plain text and markdown files

### File Upload

- **Drag & Drop**: Intuitive file upload interface
- **Progress Tracking**: Real-time upload progress with WebSocket updates
- **Error Handling**: Clear error messages for failed uploads

### Theme Support

- **Light/Dark Mode**: Toggle between light and dark themes
- **System Preference**: Automatically detects user's system theme preference

## User Experience Improvements

### Query Error Handling

The application now provides comprehensive feedback for query operations:

1. **Loading State**: A spinner is shown while the search is in progress
2. **No Results**: When no documents match the query, users see a helpful message suggesting they try different keywords or check if documents have been uploaded
3. **Error Messages**: If the API call fails, users receive a clear error message with guidance to try again
4. **Success Feedback**: When results are found, the count is displayed to provide context

### Responsive Design

- Works on desktop and mobile devices
- Adaptive layout that adjusts to screen size
- Touch-friendly interface elements

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
npm install
```

### Development Server

```bash
npm run dev
```

### Testing

```bash
npm run test
```

### Build

```bash
npm run build
```

## Architecture

The frontend is built with:

- **React 18** with TypeScript
- **Material-UI** for components and theming
- **Vite** for build tooling
- **Playwright** for end-to-end testing
- **Axios** for API communication

## API Integration

The frontend communicates with the backend through RESTful APIs:

- Document upload: `POST /api/documents/upload`
- Query search: `POST /api/query`
- WebSocket for real-time progress updates: `ws://localhost:8000/ws/upload-progress`
