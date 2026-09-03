# frozen_string_literal: true

module SacctApi
  # Custom error definitions for the renderer
  class ErrorHandler
    ERRORS = [
      'Error handler failed',
      'API down',
      'HTTPS error',
      'No recent access'
    ].freeze

    REASONS = [
      'The error handler activated when data was ok',
      'There was no valid connection to the API, or the API failed to return data',
      'See HTTPS error',
      'The user did not have any recent accesses'
    ].freeze

    def self.print(code, data)
      errors = ERRORS.dup
      reasons = REASONS.dup

      if code == 2
        errors[2] = data[:Error]
        reasons[2] = data[:Reason]
      end

      puts "Error: #{errors[code]}"
      puts "Reason: #{reasons[code]}"
    end
  end
end
