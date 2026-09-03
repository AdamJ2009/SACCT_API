# frozen_string_literal: true

require 'tty-table'

module SacctApi
  # TTY table renderer
  class Renderer
    def initialize(data)
      @data = data
    end

    def self.render(data)
      new(data).render
    end

    def render
      value = check_if_json_ok
      value > 0 ? error_handler(value) : render_values
    end

    private

    def error_handler(code)
      errors = ['Error handler failed', 'API down', 'HTTPS error', 'No recent access']
      reasons = [
        'The error handler activated when data was ok',
        'There was no valid connection to the API, or the API failed to return data',
        'See HTTPS error',
        'The user did not have any recent accesses'
      ]

      if code == 2
        errors[2] = @data[:Error]
        reasons[2] = @data[:Reason]
      end

      puts "Error: #{errors[code]}"
      puts "Reason: #{reasons[code]}"
    end

    def render_values
      efficiency_table if @data.key?(:days_back)
      quota_table if @data.key?(:quota_filesystem)
    end

    def check_if_json_ok
      return 1 if @data.nil?
      return 2 if @data.key?(:Error)
      return 3 if @data.dig(:last, :submit) =~ /^Not within \d+ days$/

      0
    end

    # Transposes data so headers sit in Column 1 and dynamic records populate adjacent columns
    def table_render(headers, rows)
      return if rows.empty?

      # Transpose rows so metric names form Column 1
      vertical_rows = headers.each_with_index.map do |header, index|
        [header] + rows.map { |row| row[index] }
      end

      # Total columns = 1 (for Metric label) + 1 for each entry in rows
      # Array.new(rows.size, '') creates the exact number of blank headers needed
      col_headers = ['Metric'] + Array.new(rows.size, '')

      table = TTY::Table.new(
        header: col_headers,
        rows: vertical_rows
      )

      puts table.render(:ascii)
      puts "\n"
    end

    def efficiency_table
      headers = ['Days', 'Job count', 'Queue Time(avg)', 'Run time(Avg)', 'CPU eff', 'Mem Eff']

      rows = @data[:days_back].map do |fs_path, fs_info|
        [
          fs_path.to_s,
          fs_info.dig(:jobs, :count),
          fs_info.dig(:jobs, :average_queue),
          fs_info.dig(:jobs, :average_time),
          fs_info.dig(:efficiency, :"cpu%"),
          fs_info.dig(:efficiency, :"mem%")
        ]
      end

      table_render(headers, rows)
    end

    def quota_table
      headers = ['Filesystem', 'Used Bytes', 'Quota Bytes', 'Limit Bytes', 'Used Files', 'Quota Files', 'Limit Files']

      rows = @data[:quota_filesystem].map do |fs_path, fs_info|
        [
          fs_path.to_s,
          fs_info.dig(:blocks, :used_bytes),
          fs_info.dig(:blocks, :quota_bytes),
          fs_info.dig(:blocks, :limit_bytes),
          fs_info.dig(:files, :used),
          fs_info.dig(:files, :quota),
          fs_info.dig(:files, :limit)
        ]
      end

      table_render(headers, rows)
    end
  end
end