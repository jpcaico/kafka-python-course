
import threading 


class SimpleLog:
    """
    Implement a simple in memory log - append only

    1. append-only writes : data can only be appended (aded) to the end
    2. immutable records : once added, data is never changed
    3. sequential reads: consumers need to read in order

    """

    def __init__(self):

        """
        records: list acting as our log segment
        lock: threading.Lock ensure only one write happens at a time (simulate how kafka guarantees ordered appends safely)


        """
        self.records = [] # hold our records
        self.lock = threading.Lock() #ensure thread-safe writes


    def append(self, record: any) -> int:
        """
        Append a new record to the end of the log

        record: any type of data you want to store
        return: the offset where the record was added
        
        """

        with self.lock:

            offset = len(self.records)
            self.records.append(record) # append to the in-memory list
            print(f"Record appended. Assigned offset {offset}")
            return offset


    def read(self, offset: int) -> any:
        """
        Read a single record from a specific offset

        offset: the records position in the log
        return: the record itself at the give offset

        """

        if offset < 0 or offset >= len(self.records):
            raise IndexError("Offset is out of bounds.")
        
        return self.records[offset]
    

    def read_from(self, start_offset: int) -> list:
        """
        Simulate that a consumer is reading the records starting from a specific offset

        start_offset: where the consumer begins reading from
        returns: list of records from start_offset till the end of the log
        
        """
        if start_offset < 0 or start_offset >= len(self.records):
            raise IndexError("Offset is out of bounds.")
        
        return self.records[start_offset:]
    

    def latest_offset(self) -> int:
        """
        Returns the latest succesfully written offset
        returns: integer represeting the last index written or -1 if the log is empty
        """

        if not self.records:
            return -1
        return len(self.records) -1 # the last valid offset
    

    def __repr__(self) -> str:
        """
        Get a representation of our log

        """

        if not self.records:
            return "Log is Empty."
        
        header = "---- Log Content ---- \n"
        lines = [f" Offset {idx}: {record}" for idx, record in enumerate(self.records)]
        footer = "\n ----- End of Log ----"
        return header + "\n".join(lines) + footer