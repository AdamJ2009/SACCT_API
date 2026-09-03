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
      puts efficiency_table if @data.key?(:days_back)
      puts job_table if @data.key?(:days_back)
      puts quota_table if @data.key?(:quota_filesystem)
    end

    def check_if_json_ok
      return 1 if @data.nil?
      return 2 if @data.key?(:Error)
      return 3 if @data.dig(:last, :submit) =~ /^Not within \d+ days$/

      0
    end

    # Transposes data so headers sit in Column 1 and dynamic records populate adjacent columns
    def table_render(headers, rows, multiline: false)
      return if rows.empty?

      table = TTY::Table.new(header: headers, rows: rows)

      # Disable automatic vertical orientation fallback and enable multiline rendering
      table.render(
        :unicode, 
        multiline: multiline,
        resize: true,
        padding: [0, 1],
      )
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

    def job_table
      headers = ["Days back", "Job Shapes Summary"]
      
      rows = @data[:days_back].map do |fs_path, fs_info|
        [
          fs_path.to_s,
          job_table_individual(fs_info)
        ]
      end

      # Pass multiline: true so TTY::Table wraps embedded string linebreaks cleanly
      table_render(headers, rows, multiline: true)
    end

    def job_table_individual(passed_data)
      shapes = passed_data.dig(:jobs, :shapes)
      return "-" if shapes.nil? || shapes.empty?

      headers = ["Type", "Count", "Avg CPU", "Avg Node", "Avg CPU/Node"]
      
      rows = shapes.map do |fs_path, fs_info|
        [
          fs_path.to_s,
          fs_info[:count],
          fs_info.fetch(:avg_cpu, '-'),
          fs_info.fetch(:avg_node, '-'),
          fs_info.fetch(:avg_cpu_per_node, '-')
        ]
      end

      # Build the inner sub-table WITHOUT borders to prevent outer table distortion
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