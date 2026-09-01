# frozen_string_literal: true

require 'bundler/setup'
require 'date'
require 'dry/cli'
require 'fileutils'
require 'json'
require 'yaml'

require_relative 'version'
require_relative '../config/configmanager'

module Sacct_api
  module CLI
    module Commands
      extend Dry::CLI::Registry

      module Config
        class Set < Dry::CLI::Command
          desc 'Save API configuration settings'
          option :url, aliases:['-u'], type: :string, desc: 'API base URL'
          option :ssl, alaises:['-s'], type: :boolean, desc: 'Verify SSL certificate'

          def call(**opts)
            current = ConfigManager.load
            new_url = opts[:url] || current['url']
            new_ssl = opts.key?(:ssl) ? opts[:ssl] : current['ssl']

            ConfigManager.save(url: new_url, ssl: new_ssl)
          end
        end

        class Show < Dry::CLI::Command
          desc 'Display current API configuration settings'

          def call(**)
            config = ConfigManager.load
            puts "Config File: #{ConfigManager::CONFIG_FILE}"
            puts "URL:         #{config['url']}"
            puts "SSL Verify:  #{config['ssl']}"
          end
        end
      end

      class Report < Dry::CLI::Command
        desc 'Report based on flags sent to the cli'
        option :days, aliases:['-d','--date'], type: :integer, desc: 'Go back n amount of days'
        option :timespread, aliases:["-t","--times"], type: :boolean, desc: "Show 7,30,90 days"
        option :user, aliases:['-u','--username'], type: :string, desc: "Select user(leave blank for self)"
        option :json, aliases:["-j"], type: :string, desc: "Save json if not none"
        
        def call(**opts)
          user = opts[:user].nil? ? current_user : opts[:user]
          days = opts[:days].nil? ? 30 : opts[:days]
          result = opts[:timespread] ? timespread(user) : single_time(user,days)
          unless json.nil?
            json = json_check(opts[:json])
            File.write(json,JSON.dump(result))
          end
        end

        private
        def current_user
          Etc.getlogin || ENV['USER'] || ENV['LOGNAME'] || Etc.getpwuid(Process.uid)&.name
        rescue StandardError
          ENV['USER']
        end

        def timespread(user)
          cmd = "curl " + get_url + "/user/" + user
          result = `#{cmd}`
        end

        def single_time(user,days)
          cmd = "curl " + get_url + "/user/" + user + "/" + days.to_s
          result = `#{cmd}`
        end

        def get_url
          config = ConfigManager.load
          url = config['url']
          ssl = config['ssl'] ? '' : '-k '
          return ssl + url 
        end
      end

      class Version < Dry::CLI::Command
        desc 'Print the version'

        def call(*)
          puts "SacctAPI version #{Sacct_api::VERSION}"
        end
      end
      register 'report', Report
      register 'config set', Config::Set
      register 'config show', Config::Show
      register 'version', Version, aliases: ['-v', '--version']
    end
  end
end

