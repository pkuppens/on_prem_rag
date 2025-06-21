type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  filename: string;
  functionName: string;
  lineNumber: number;
  data?: unknown;
}

class Logger {
  private static formatTimestamp(): string {
    return new Date().toISOString();
  }

  private static formatLogEntry(
    level: LogLevel,
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): LogEntry {
    return {
      timestamp: this.formatTimestamp(),
      level,
      message,
      filename,
      functionName,
      lineNumber,
      data,
    };
  }

  private static log(
    level: LogLevel,
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): void {
    const entry = this.formatLogEntry(
      level,
      message,
      filename,
      functionName,
      lineNumber,
      data
    );

    // In development, use console with colors
    if (import.meta.env.DEV) {
      const colors = {
        info: '\x1b[32m', // Green
        warn: '\x1b[33m', // Yellow
        error: '\x1b[31m', // Red
        debug: '\x1b[36m', // Cyan
      };
      const reset = '\x1b[0m';

      console.log(
        `${colors[level]}[${entry.timestamp}] ${entry.level.toUpperCase()}: ${
          entry.message
        } (${entry.filename}:${entry.functionName}:${entry.lineNumber})${
          data ? `\nData: ${JSON.stringify(data, null, 2)}` : ''
        }${reset}`
      );
    } else {
      // In production, use structured logging
      console.log(JSON.stringify(entry));
    }
  }

  static info(
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): void {
    this.log('info', message, filename, functionName, lineNumber, data);
  }

  static warn(
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): void {
    this.log('warn', message, filename, functionName, lineNumber, data);
  }

  static error(
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): void {
    this.log('error', message, filename, functionName, lineNumber, data);
  }

  static debug(
    message: string,
    filename: string,
    functionName: string,
    lineNumber: number,
    data?: unknown
  ): void {
    if (import.meta.env.DEV) {
      this.log('debug', message, filename, functionName, lineNumber, data);
    }
  }
}

export default Logger;
