import argparse
import redis
import os

class DataStore:
    def __init__(self, host='localhost', port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db)

    def add_domain(self, project, domain):
        return self.r.sadd(project, domain)

    def get_domains(self, project):
        return self.r.smembers(project)

    def deduplicate(self, project):
        # Since we're using a set in Redis, it automatically takes care of deduplication
        pass

class Project:
    def __init__(self, datastore, name):
        self.datastore = datastore
        self.name = name

    def add_domains_from_file(self, filename):
        if not os.path.exists(filename):
            print("File {} does not exist.".format(filename))
            return
        with open(filename, 'r') as file:
            total_domains = 0
            new_domains = 0
            for line in file:
                domain = line.strip()
                added = self.datastore.add_domain(self.name, domain)
                total_domains += 1
                new_domains += added
            duplicate_domains = total_domains - new_domains
            if total_domains > 0:  # To avoid division by zero
                duplicate_percentage = (duplicate_domains / total_domains) * 100
            else:
                duplicate_percentage = 0
            print("{} out of {} domains were duplicates ({:.2f}%).".format(duplicate_domains, total_domains, duplicate_percentage))

    def get_domains(self):
        return self.datastore.get_domains(self.name)

    def deduplicate(self):
        self.datastore.deduplicate(self.name)

def main():
    parser = argparse.ArgumentParser(description="Manage bug bounty targets")
    parser.add_argument('-p', '--project', required=True, help='The project name')
    parser.add_argument('-f', '--file', help='The file containing domains')
    parser.add_argument('-o', '--operation', required=True, choices=['add', 'print'], help='Operation to perform')
    args = parser.parse_args()

    datastore = DataStore()
    project = Project(datastore, args.project)

    if args.operation == 'add':
        if args.file is None:
            print("You must provide a file with the 'add' operation.")
            return
        project.add_domains_from_file(args.file)
        project.deduplicate()
    elif args.operation == 'print':
        domains = project.get_domains()
        for domain in domains:
            print(domain.decode('utf-8'))  # Redis returns bytes, so we need to decode them to strings

if __name__ == '__main__':
    main()
