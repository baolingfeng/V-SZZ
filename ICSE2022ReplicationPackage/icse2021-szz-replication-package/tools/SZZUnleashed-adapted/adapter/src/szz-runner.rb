require 'tempfile'
require 'tmpdir'
require 'logger'
require 'code-assertions'

require_relative 'issue-trackers'

PROJECT_DIR = File.dirname(File.expand_path(File.join(__FILE__, "../..")))
TIMEOUT     = 60 * 60 * 72 # 72 hour timeout

class Dir
    def self.mkmytmpdir(tmp_root)
        self.mktmpdir do |name|
            begin
                my_name = name.sub("/tmp", tmp_root)
                assert("#{my_name} should not exist.") { !FileTest.exist?(my_name) }
                puts "Temp dir #{my_name}"
                `mkdir -p "#{my_name}"`
                yield my_name
            ensure 
                FileUtils.rm_rf(my_name)
            end
        end
    end
end

class FixCommit
    attr_accessor   :hash
    attr_accessor   :issue_date
    attr_accessor   :issue_url
end

class FixIntroducingPair
    attr_accessor   :fix_hash
    attr_accessor   :introducing_hash
    
    def initialize(fix_hash, introducing_hash)
        @fix_hash = fix_hash
        @introducing_hash = introducing_hash
    end
end

class SZZUnleashed
    LOGGER = Logger.new(STDOUT)
        
    GIT_LOG_TO_ARRAY = File.join(PROJECT_DIR, "fetch_jira_bugs/git_log_to_array.py")
    SZZ_DIR          = File.join(PROJECT_DIR, "szz")
    SZZ_JAR          = File.join(SZZ_DIR, "build/libs/szz_find_bug_introducers-0.1.jar")
    
    @@max_cores      = nil
    @@tmp_root       = nil
    
    def self.setup(max_cores, tmp_root)
        @@tmp_root  = tmp_root
        LOGGER.info("Using tmp root #{@@tmp_root}")
        @@max_cores = max_cores
        if @@max_cores != nil
            LOGGER.info("Max number of cores: #{@@max_cores}")
        else
            LOGGER.warn("Using all the cores. This is not recommended.")
        end
    end
    
    def self.build
        unless FileTest.exist? SZZ_JAR
            Dir.chdir(SZZ_DIR) do
                `gradle build && gradle fatJar`
                assert("The target JAR file should exist at this point; probably, the build failed") { FileTest.exists?(SZZ_JAR) }
            end
            return true
        else
            return false
        end
    end
        
    def self.run_pipeline(repository_path, fix_commits)
        Dir.mkmytmpdir(@@tmp_root) do |working_dir|
            LOGGER.info "Starting the run pipeline for #{repository_path} for #{fix_commits.size} issues"
            
            repository_folder = File.join(working_dir, "repository")
            log_filename      = File.join(repository_folder, "gitlog.json")
            issues_filename   = File.join(working_dir, "issues.json")
            
            if self.build
                LOGGER.info "SZZ build completed."
            else
                LOGGER.info "Skipping build, re-using existing JAR at #{SZZ_JAR}; remove it to force re-build"
            end
            
            LOGGER.info "Generating issue file at #{issues_filename}"
            self.generate_issue_file(fix_commits, issues_filename)
            
            LOGGER.info "Cloning repository and generating log array at #{repository_folder}"
            self.generate_git_log(repository_path, repository_folder)
            
            LOGGER.info "Running SZZ Unleashed"
            result = self.run_szz(working_dir, repository_folder, log_filename, issues_filename)
            
            LOGGER.info "Run completed for #{repository_path}"
            
            return result
        end
    end
    
    def self.generate_git_log(repository_path, local_repository)
        if repository_path.start_with? "http"
            LOGGER.info "Cloning remote repository"
            `git clone "#{repository_path}" #{local_repository}`
        elsif FileTest.directory? repository_path
            LOGGER.info "Copying local repository"
            `cp -r "#{repository_path}" "#{local_repository}"`
        else
            LOGGER.error "The repository #{repository_path} does not exist."
            raise "The repository does not exist"
        end
        
        Dir.chdir(File.dirname(local_repository)) do
            `python3 "#{GIT_LOG_TO_ARRAY}" --repo-path "#{local_repository}" --from-commit master`
        end
    end
    
    def self.generate_issue_file(fix_commits, issues_filename)
        result = []
        fix_commits.each do |commit|
            if commit.issue_date
                LOGGER.info("Using cached date, not fetching it...")
                issue = Issue.new(commit.issue_url, commit.issue_date)
            else
                LOGGER.info("Fetching date from the issue tracker")
                issue = IssueTracker.handler_for(commit.issue_url).fetch(commit.issue_url)
            end
            issue.hash = commit.hash
            
            # Save issue json to file
            result << issue
        end
        
        File.open(issues_filename, 'w') do |f|
            issues = {}
            result.each do |issue|
                issues[issue.id] = issue.to_h
            end
            
            f.puts JSON.generate(issues)
        end
    end
    
    def self.run_szz(working_dir, repository_folder, log_filename, issues_filename)
        Dir.chdir(working_dir) do 
            core_opt = @@max_cores ? "-c #{@@max_cores}" : nil
            
            opts = [core_opt].select { |e| e != nil }.join(" ")
            
            command = "java -jar \"#{SZZ_JAR}\" -i \"#{issues_filename}\" -r \"#{repository_folder}\" #{opts}"
            
            result  = []
            pid     = Process.spawn(command)
            
            LOGGER.info("Started process for command: \"#{command}\" (pid: #{pid})")
            begin
                Timeout.timeout(TIMEOUT) do
                    Process.wait(pid)
                    
                    temporary_result = JSON.parse(File.read("results/fix_and_introducers_pairs.json"))
                    temporary_result.each do |pair|
                        result << FixIntroducingPair.new(pair[0], pair[1])
                    end
                end
            rescue Timeout::Error
                LOGGER.warn("The process did not finish in time. Killing.")
                Process.kill('KILL', pid)
            end
            
            return result
        end
    end
end
