# Get a unique list of people from the collective org charts
cat orgs/pubsector/*.json  | jq '.results[] | [.username, .user.full_name, .user.building, .user.job_title, .user.department_name] | @tsv' -r | sort | uniq > people.tsv
# Get the usernames only
cut -f 1 people.tsv > username.txt
# Fetch thhose unique people
mkdir -p images
while read p; do
  curl -o images/$p.jpeg  https://internal-cdn.amazon.com/badgephotos.amazon.com/?uid=$p
done <username.txt
